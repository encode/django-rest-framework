"""
Customizable serialization.
"""
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField
from django.utils.encoding import smart_unicode

import decimal
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
    Return a list of field names.
    """
    return [_field_to_tuple(field)[0] for field in fields or ()]

def _fields_to_dict(fields):
    """
    Return a `dict` of field name -> None, or tuple of fields, or Serializer class
    """
    return dict([_field_to_tuple(field) for field in fields or ()])


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


    def __init__(self, depth=None, stack=[], **kwargs):
        self.depth = depth or self.depth
        self.stack = stack
        

    def get_fields(self, obj):
        """
        Return the set of field names/keys to use for a model instance/dict.
        """
        fields = self.fields

        # If `fields` is not set, we use the default fields and modify
        # them with `include` and `exclude`
        if not fields:
            default = self.get_default_fields(obj)
            include = self.include or ()
            exclude = self.exclude or ()
            fields = set(default + list(include)) - set(exclude)

        else:
            fields = _fields_to_list(self.fields)

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


    def get_related_serializer(self, key):
        info = _fields_to_dict(self.fields).get(key, None)

        # If an element in `fields` is a 2-tuple of (str, tuple)
        # then the second element of the tuple is the fields to
        # set on the related serializer
        if isinstance(info, (list, tuple)):
            class OnTheFlySerializer(Serializer):
                fields = info
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
        
        # Otherwise use `related_serializer` or fall back to `Serializer`
        return getattr(self, 'related_serializer') or Serializer


    def serialize_key(self, key):
        """
        Keys serialize to their string value,
        unless they exist in the `rename` dict.
        """
        return getattr(self.rename, key, key)


    def serialize_val(self, key, obj):
        """
        Convert a model field or dict value into a serializable representation.
        """
        related_serializer = self.get_related_serializer(key)
     
        if self.depth is None:
            depth = None
        elif self.depth <= 0:
            return self.serialize_max_depth(obj)
        else:
            depth = self.depth - 1

        if any([obj is elem for elem in self.stack]):
            return self.serialize_recursion(obj)
        else:
            stack = self.stack[:]
            stack.append(obj)

        return related_serializer(depth=depth, stack=stack).serialize(obj)


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

        fields = self.get_fields(instance)

        # serialize each required field 
        for fname in fields:
            if hasattr(self, fname):
                # check for a method 'fname' on self first
                meth = getattr(self, fname)
                if inspect.ismethod(meth) and len(inspect.getargspec(meth)[0]) == 2:
                    obj = meth(instance)
            elif hasattr(instance, fname):
                # now check for an attribute 'fname' on the instance
                obj = getattr(instance, fname)
            elif fname in instance:
                # finally check for a key 'fname' on the instance
                obj = instance[fname]
            else:
                continue

            try:
                key = self.serialize_key(fname)
                val = self.serialize_val(fname, obj)
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


    def serialize_decimal(self, obj):
        """
        Convert a Decimal instance into a serializable representation.
        """
        return str(obj)


    def serialize_fallback(self, obj):
        """
        Convert any unhandled object into a serializable representation.
        """
        return smart_unicode(obj, strings_only=True)
 
 
    def serialize(self, obj):
        """
        Convert any object into a serializable representation.
        """
        
        if isinstance(obj, (dict, models.Model)):
            # Model instances & dictionaries
            return self.serialize_model(obj)
        elif isinstance(obj, (tuple, list, set, QuerySet, types.GeneratorType)):
            # basic iterables
            return self.serialize_iter(obj)
        elif isinstance(obj, models.Manager):
            # Manager objects
            return self.serialize_manager(obj)
        elif isinstance(obj, decimal.Decimal):
            # Decimals (force to string representation)
            return self.serialize_decimal(obj)
        elif inspect.isfunction(obj) and not inspect.getargspec(obj)[0]:
            # function with no args
            return self.serialize_func(obj)
        elif inspect.ismethod(obj) and len(inspect.getargspec(obj)[0]) <= 1:
            # bound method
            return self.serialize_func(obj)

        # fall back to smart unicode
        return self.serialize_fallback(obj)
