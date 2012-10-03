import copy
import datetime
import types
from decimal import Decimal
from django.core.serializers.base import DeserializedObject
from django.db import models
from django.utils.datastructures import SortedDict
from rest_framework.compat import get_concrete_model
from rest_framework.fields import *


class DictWithMetadata(dict):
    """
    A dict-like object, that can have additional properties attached.
    """
    pass


class SortedDictWithMetadata(SortedDict, DictWithMetadata):
    """
    A sorted dict-like object, that can have additional properties attached.
    """
    pass


class RecursionOccured(BaseException):
    pass


def _is_protected_type(obj):
    """
    True if the object is a native datatype that does not need to
    be serialized further.
    """
    return isinstance(obj, (
        types.NoneType,
       int, long,
       datetime.datetime, datetime.date, datetime.time,
       float, Decimal,
       basestring)
    )


def _get_declared_fields(bases, attrs):
    """
    Create a list of serializer field instances from the passed in 'attrs',
    plus any fields on the base classes (in 'bases').

    Note that all fields from the base classes are used.
    """
    fields = [(field_name, attrs.pop(field_name))
              for field_name, obj in attrs.items()
              if isinstance(obj, Field)]
    fields.sort(key=lambda x: x[1].creation_counter)

    # If this class is subclassing another Serializer, add that Serializer's
    # fields.  Note that we loop over the bases in *reverse*. This is necessary
    # in order to the correct order of fields.
    for base in bases[::-1]:
        if hasattr(base, 'base_fields'):
            fields = base.base_fields.items() + fields

    return SortedDict(fields)


class SerializerMetaclass(type):
    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = _get_declared_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


class SerializerOptions(object):
    """
    Meta class options for Serializer
    """
    def __init__(self, meta):
        self.nested = getattr(meta, 'nested', False)
        self.fields = getattr(meta, 'fields', ())
        self.exclude = getattr(meta, 'exclude', ())


class BaseSerializer(Field):
    class Meta(object):
        pass

    _options_class = SerializerOptions
    _dict_class = SortedDictWithMetadata  # Set to unsorted dict for backwards compatability with unsorted implementations.

    def __init__(self, data=None, instance=None, context=None, **kwargs):
        super(BaseSerializer, self).__init__(**kwargs)
        self.fields = copy.deepcopy(self.base_fields)
        self.opts = self._options_class(self.Meta)
        self.parent = None
        self.root = None

        self.stack = []
        self.context = context or {}

        self.init_data = data
        self.object = instance

        self._data = None
        self._errors = None

    #####
    # Methods to determine which fields to use when (de)serializing objects.

    def default_fields(self, serialize, obj=None, data=None, nested=False):
        """
        Return the complete set of default fields for the object, as a dict.
        """
        return {}

    def get_fields(self, serialize, obj=None, data=None, nested=False):
        """
        Returns the complete set of fields for the object as a dict.

        This will be the set of any explicitly declared fields,
        plus the set of fields returned by default_fields().
        """
        ret = SortedDict()

        # Get the explicitly declared fields
        for key, field in self.fields.items():
            ret[key] = field
            # Determine if the declared field corrosponds to a model field.
            try:
                if key == 'pk':
                    model_field = obj._meta.pk
                else:
                    model_field = obj._meta.get_field_by_name(key)[0]
            except:
                model_field = None
            # Set up the field
            field.initialize(parent=self, model_field=model_field)

        # Add in the default fields
        fields = self.default_fields(serialize, obj, data, nested)
        for key, val in fields.items():
            if key not in ret:
                ret[key] = val

        # If 'fields' is specified, use those fields, in that order.
        if self.opts.fields:
            new = SortedDict()
            for key in self.opts.fields:
                new[key] = ret[key]
            ret = new

        # Remove anything in 'exclude'
        if self.opts.exclude:
            for key in self.opts.exclude:
                ret.pop(key, None)

        return ret

    #####
    # Field methods - used when the serializer class is itself used as a field.

    def initialize(self, parent, model_field=None):
        """
        Same behaviour as usual Field, except that we need to keep track
        of state so that we can deal with handling maximum depth and recursion.
        """
        super(BaseSerializer, self).initialize(parent, model_field)
        self.stack = parent.stack[:]
        if parent.opts.nested and not isinstance(parent.opts.nested, bool):
            self.opts.nested = parent.opts.nested - 1
        else:
            self.opts.nested = parent.opts.nested

    #####
    # Methods to convert or revert from objects <--> primative representations.

    def get_field_key(self, field_name):
        """
        Return the key that should be used for a given field.
        """
        return field_name

    def convert_object(self, obj):
        """
        Core of serialization.
        Convert an object into a dictionary of serialized field values.
        """
        if obj in self.stack and not self.source == '*':
            raise RecursionOccured()
        self.stack.append(obj)

        ret = self._dict_class()
        ret.fields = {}

        fields = self.get_fields(serialize=True, obj=obj, nested=self.opts.nested)
        for field_name, field in fields.items():
            key = self.get_field_key(field_name)
            try:
                value = field.field_to_native(obj, field_name)
            except RecursionOccured:
                field = self.get_fields(serialize=True, obj=obj, nested=False)[field_name]
                value = field.field_to_native(obj, field_name)
            ret[key] = value
            ret.fields[key] = field
        return ret

    def restore_fields(self, data):
        """
        Core of deserialization, together with `restore_object`.
        Converts a dictionary of data into a dictionary of deserialized fields.
        """
        fields = self.get_fields(serialize=False, data=data, nested=self.opts.nested)
        reverted_data = {}
        for field_name, field in fields.items():
            try:
                field.field_from_native(data, field_name, reverted_data)
            except ValidationError as err:
                self._errors[field_name] = list(err.messages)

        return reverted_data

    def restore_object(self, attrs, instance=None):
        """
        Deserialize a dictionary of attributes into an object instance.
        You should override this method to control how deserialized objects
        are instantiated.
        """
        if instance is not None:
            instance.update(attrs)
            return instance
        return attrs

    def to_native(self, obj):
        """
        Serialize objects -> primatives.
        """
        if isinstance(obj, DeserializedObject):
            obj = obj.object

        if isinstance(obj, dict):
            return dict([(key, self.to_native(val))
                         for (key, val) in obj.items()])
        elif hasattr(obj, '__iter__'):
            return [self.to_native(item) for item in obj]
        return self.convert_object(obj)

    def from_native(self, data):
        """
        Deserialize primatives -> objects.
        """
        if hasattr(data, '__iter__') and not isinstance(data, dict):
            # TODO: error data when deserializing lists
            return (self.from_native(item) for item in data)
        self._errors = {}
        attrs = self.restore_fields(data)
        if not self._errors:
            return self.restore_object(attrs, instance=getattr(self, 'object', None))

    @property
    def errors(self):
        """
        Run deserialization and return error data,
        setting self.object if no errors occured.
        """
        if self._errors is None:
            obj = self.from_native(self.init_data)
            if not self._errors:
                self.object = obj
        return self._errors

    def is_valid(self):
        return not self.errors

    @property
    def data(self):
        if self._data is None:
            self._data = self.to_native(self.object)
        return self._data


class Serializer(BaseSerializer):
    __metaclass__ = SerializerMetaclass


class ModelSerializerOptions(SerializerOptions):
    """
    Meta class options for ModelSerializer
    """
    def __init__(self, meta):
        super(ModelSerializerOptions, self).__init__(meta)
        self.model = getattr(meta, 'model', None)


class ModelSerializer(RelatedField, Serializer):
    """
    A serializer that deals with model instances and querysets.
    """
    _options_class = ModelSerializerOptions

    def default_fields(self, serialize, obj=None, data=None, nested=False):
        """
        Return all the fields that should be serialized for the model.
        """
        cls = self.opts.model
        opts = get_concrete_model(cls)._meta
        pk_field = opts.pk
        while pk_field.rel:
            pk_field = pk_field.rel.to._meta.pk
        fields = [pk_field]
        fields += [field for field in opts.fields if field.serialize]
        fields += [field for field in opts.many_to_many if field.serialize]

        ret = SortedDict()
        is_pk = True  # First field in the list is the pk

        for model_field in fields:
            if is_pk:
                field = self.get_pk_field(model_field)
                is_pk = False
            elif model_field.rel and nested:
                field = self.get_nested_field(model_field)
            elif model_field.rel:
                field = self.get_related_field(model_field)
            else:
                field = self.get_field(model_field)

            if field:
                field.initialize(parent=self, model_field=model_field)
                ret[model_field.name] = field

        return ret

    def get_pk_field(self, model_field):
        """
        Returns a default instance of the pk field.
        """
        return Field(readonly=True)

    def get_nested_field(self, model_field):
        """
        Creates a default instance of a nested relational field.
        """
        return ModelSerializer()

    def get_related_field(self, model_field):
        """
        Creates a default instance of a flat relational field.
        """
        return PrimaryKeyRelatedField()

    def get_field(self, model_field):
        """
        Creates a default instance of a basic non-relational field.
        """
        field_mapping = dict([
            [models.FloatField, FloatField],
            [models.IntegerField, IntegerField],
            [models.DateTimeField, DateTimeField],
            [models.DateField, DateField],
            [models.EmailField, EmailField],
            [models.CharField, CharField],
            [models.CommaSeparatedIntegerField, CharField],
            [models.BooleanField, BooleanField]
        ])
        try:
            return field_mapping[model_field.__class__]()
        except KeyError:
            return Field()

    def restore_object(self, attrs, instance=None):
        """
        Restore the model instance.
        """
        if instance:
            for key, val in attrs.items():
                setattr(instance, key, val)
            return DeserializedObject(instance)

        m2m_data = {}
        for field in self.opts.model._meta.many_to_many:
            if field.name in attrs:
                m2m_data[field.name] = attrs.pop(field.name)
        return DeserializedObject(self.opts.model(**attrs), m2m_data)
