"""
Customizable serialization.
"""
from django.db import models
from django.db.models.query import QuerySet, RawQuerySet
from django.utils.encoding import smart_unicode, is_protected_type, smart_str

import inspect
import types


# We register serializer classes, so that we can refer to them by their
# class names, if there are cyclical serialization heirachys.
_serializers = {}


def _field_to_tuple(field):
    """
    Convert an item in the `fields` attribute into a 2-tuple.
    """
    if isinstance(field, (tuple, list)):
        return (field[0], field[1])
    return (field, None)


def _fields_to_list(fields):
    """
    Return a list of field tuples.
    """
    return [_field_to_tuple(field) for field in fields or ()]


class _SkipField(Exception):
    """
    Signals that a serialized field should be ignored.
    We use this mechanism as the default behavior for ensuring
    that we don't infinitely recurse when dealing with nested data.
    """
    pass


class _RegisterSerializer(type):
    """
    Metaclass to register serializers.
    """
    def __new__(cls, name, bases, attrs):
        # Build the class and register it.
        ret = super(_RegisterSerializer, cls).__new__(cls, name, bases, attrs)
        _serializers[name] = ret
        return ret


class Serializer(object):
    """
    Converts python objects into plain old native types suitable for
    serialization.  In particular it handles models and querysets.

    The output format is specified by setting a number of attributes
    on the class.

    You may also override any of the serialization methods, to provide
    for more flexible behavior.

    Valid output types include anything that may be directly rendered into
    json, xml etc...
    """
    __metaclass__ = _RegisterSerializer

    fields = ()
    """
    Specify the fields to be serialized on a model or dict.
    Overrides `include` and `exclude`.
    """

    include = ()
    """
    Fields to add to the default set to be serialized on a model/dict.
    """

    exclude = ()
    """
    Fields to remove from the default set to be serialized on a model/dict.
    """

    rename = {}
    """
    A dict of key->name to use for the field keys.
    """

    related_serializer = None
    """
    The default serializer class to use for any related models.
    """

    depth = None
    """
    The maximum depth to serialize to, or `None`.
    """
    
    parent = None
    """
    A reference to the root serializer when descending down into fields.
    """

    def __init__(self, depth=None, stack=[], **kwargs):
        if depth is not None:
            self.depth = depth
        self.stack = stack

    def get_fields(self, obj):
        fields = self.fields

        # If `fields` is not set, we use the default fields and modify
        # them with `include` and `exclude`
        if not fields:
            default = self.get_default_fields(obj)
            include = self.include or ()
            exclude = self.exclude or ()
            fields = set(default + list(include)) - set(exclude)

        return fields

    def get_default_fields(self, obj):
        """
        Return the default list of field names/keys for a model instance/dict.
        These are used if `fields` is not given.
        """
        if isinstance(obj, models.Model):
            opts = obj._meta
            return [field.name for field in opts.fields + opts.many_to_many]
        else:
            return obj.keys()

    def get_related_serializer(self, info):
        # If an element in `fields` is a 2-tuple of (str, tuple)
        # then the second element of the tuple is the fields to
        # set on the related serializer

        class OnTheFlySerializer(self.__class__):
            fields = info
            parent = getattr(self, 'parent') or self

        if isinstance(info, (list, tuple)):
            return OnTheFlySerializer

        # If an element in `fields` is a 2-tuple of (str, Serializer)
        # then the second element of the tuple is the Serializer
        # class to use for that field.
        elif isinstance(info, type) and issubclass(info, Serializer):
            return info

        # If an element in `fields` is a 2-tuple of (str, str)
        # then the second element of the tuple is the name of the Serializer
        # class to use for that field.
        #
        # Black magic to deal with cyclical Serializer dependancies.
        # Similar to what Django does for cyclically related models.
        elif isinstance(info, str) and info in _serializers:
            return _serializers[info]

        # Otherwise use `related_serializer` or fall back to
        # `OnTheFlySerializer` preserve custom serialization methods.
        return getattr(self, 'related_serializer') or OnTheFlySerializer

    def serialize_key(self, key):
        """
        Keys serialize to their string value,
        unless they exist in the `rename` dict.
        """
        return self.rename.get(smart_str(key), smart_str(key))

    def serialize_val(self, key, obj, related_info):
        """
        Convert a model field or dict value into a serializable representation.
        """
        related_serializer = self.get_related_serializer(related_info)

        if self.depth is None:
            depth = None
        elif self.depth <= 0:
            return self.serialize_max_depth(obj)
        else:
            depth = self.depth - 1

        if obj in self.stack:
            return self.serialize_recursion(obj)
        else:
            stack = self.stack[:]
            stack.append(obj)

        return related_serializer(depth=depth, stack=stack).serialize(
            obj, request=getattr(self, 'request', None))

    def serialize_max_depth(self, obj):
        """
        Determine how objects should be serialized once `depth` is exceeded.
        The default behavior is to ignore the field.
        """
        raise _SkipField

    def serialize_recursion(self, obj):
        """
        Determine how objects should be serialized if recursion occurs.
        The default behavior is to ignore the field.
        """
        raise _SkipField

    def serialize_model(self, instance):
        """
        Given a model instance or dict, serialize it to a dict..
        """
        data = {}
        # Append the instance itself to the stack so that you never iterate
        # back into the first object.
        self.stack.append(instance)

        fields = self.get_fields(instance)

        # serialize each required field
        for fname, related_info in _fields_to_list(fields):
            try:
                # we first check for a method 'fname' on self,
                # 'fname's signature must be 'def fname(self, instance)'
                meth = getattr(self, fname, None)
                if (inspect.ismethod(meth) and
                            len(inspect.getargspec(meth)[0]) == 2):
                    obj = meth(instance)
                elif hasattr(instance, '__contains__') and fname in instance:
                    # then check for a key 'fname' on the instance
                    obj = instance[fname]
                elif hasattr(instance, smart_str(fname)):
                    # finally check for an attribute 'fname' on the instance
                    obj = getattr(instance, fname)
                else:
                    continue

                key = self.serialize_key(fname)
                val = self.serialize_val(fname, obj, related_info)
                data[key] = val
            except _SkipField:
                pass

        return data

    def serialize_iter(self, obj):
        """
        Convert iterables into a serializable representation.
        """
        return [self.serialize(item) for item in obj]

    def serialize_func(self, obj):
        """
        Convert no-arg methods and functions into a serializable representation.
        """
        return self.serialize(obj())

    def serialize_manager(self, obj):
        """
        Convert a model manager into a serializable representation.
        """
        return self.serialize_iter(obj.all())

    def serialize_fallback(self, obj):
        """
        Convert any unhandled object into a serializable representation.
        """
        return smart_unicode(obj, strings_only=True)

    def serialize(self, obj, request=None):
        """
        Convert any object into a serializable representation.
        """

        # Request from related serializer.
        if request is not None:
            self.request = request

        if isinstance(obj, (dict, models.Model)):
            # Model instances & dictionaries
            return self.serialize_model(obj)
        elif isinstance(obj, (tuple, list, set, QuerySet, RawQuerySet, types.GeneratorType)):
            # basic iterables
            return self.serialize_iter(obj)
        elif isinstance(obj, models.Manager):
            # Manager objects
            return self.serialize_manager(obj)
        elif inspect.isfunction(obj) and not inspect.getargspec(obj)[0]:
            # function with no args
            return self.serialize_func(obj)
        elif inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) <= 1:
            # bound method
            return self.serialize_func(obj)

        # Protected types are passed through as is.
        # (i.e. Primitives like None, numbers, dates, and Decimals.)
        if is_protected_type(obj):
            return obj

        # All other values are converted to string.
        return self.serialize_fallback(obj)
