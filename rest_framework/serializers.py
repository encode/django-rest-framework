"""
Serializers and ModelSerializers are similar to Forms and ModelForms.
Unlike forms, they are not constrained to dealing with HTML output, and
form encoded input.

Serialization in REST framework is a two-phase process:

1. Serializers marshal between complex types like model instances, and
python primatives.
2. The process of marshalling between python primatives and request and
response content is handled by parsers and renderers.
"""
from __future__ import unicode_literals
import copy
import datetime
import types
from decimal import Decimal
from django.core.paginator import Page
from django.db import models
from django.forms import widgets
from django.utils.datastructures import SortedDict
from rest_framework.compat import get_concrete_model, six

# Note: We do the following so that users of the framework can use this style:
#
#     example_field = serializers.CharField(...)
#
# This helps keep the separation between model fields, form fields, and
# serializer fields more explicit.

from rest_framework.relations import *
from rest_framework.fields import *


class NestedValidationError(ValidationError):
    """
    The default ValidationError behavior is to stringify each item in the list
    if the messages are a list of error messages.

    In the case of nested serializers, where the parent has many children,
    then the child's `serializer.errors` will be a list of dicts.  In the case
    of a single child, the `serializer.errors` will be a dict.

    We need to override the default behavior to get properly nested error dicts.
    """

    def __init__(self, message):
        if isinstance(message, dict):
            self.messages = [message]
        else:
            self.messages = message


class DictWithMetadata(dict):
    """
    A dict-like object, that can have additional properties attached.
    """
    def __getstate__(self):
        """
        Used by pickle (e.g., caching).
        Overridden to remove the metadata from the dict, since it shouldn't be
        pickled and may in some instances be unpickleable.
        """
        return dict(self)


class SortedDictWithMetadata(SortedDict):
    """
    A sorted dict-like object, that can have additional properties attached.
    """
    def __getstate__(self):
        """
        Used by pickle (e.g., caching).
        Overriden to remove the metadata from the dict, since it shouldn't be
        pickle and may in some instances be unpickleable.
        """
        return SortedDict(self).__dict__


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
              for field_name, obj in list(six.iteritems(attrs))
              if isinstance(obj, Field)]
    fields.sort(key=lambda x: x[1].creation_counter)

    # If this class is subclassing another Serializer, add that Serializer's
    # fields.  Note that we loop over the bases in *reverse*. This is necessary
    # in order to maintain the correct order of fields.
    for base in bases[::-1]:
        if hasattr(base, 'base_fields'):
            fields = list(base.base_fields.items()) + fields

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
        self.depth = getattr(meta, 'depth', 0)
        self.fields = getattr(meta, 'fields', ())
        self.exclude = getattr(meta, 'exclude', ())


class BaseSerializer(WritableField):
    """
    This is the Serializer implementation.
    We need to implement it as `BaseSerializer` due to metaclass magicks.
    """
    class Meta(object):
        pass

    _options_class = SerializerOptions
    _dict_class = SortedDictWithMetadata

    def __init__(self, instance=None, data=None, files=None,
                 context=None, partial=False, many=None,
                 allow_add_remove=False, **kwargs):
        super(BaseSerializer, self).__init__(**kwargs)
        self.opts = self._options_class(self.Meta)
        self.parent = None
        self.root = None
        self.partial = partial
        self.many = many
        self.allow_add_remove = allow_add_remove

        self.context = context or {}

        self.init_data = data
        self.init_files = files
        self.object = instance
        self.fields = self.get_fields()

        self._data = None
        self._files = None
        self._errors = None
        self._deleted = None

        if many and instance is not None and not hasattr(instance, '__iter__'):
            raise ValueError('instance should be a queryset or other iterable with many=True')

        if allow_add_remove and not many:
            raise ValueError('allow_add_remove should only be used for bulk updates, but you have not set many=True')

    #####
    # Methods to determine which fields to use when (de)serializing objects.

    def get_default_fields(self):
        """
        Return the complete set of default fields for the object, as a dict.
        """
        return {}

    def get_fields(self):
        """
        Returns the complete set of fields for the object as a dict.

        This will be the set of any explicitly declared fields,
        plus the set of fields returned by get_default_fields().
        """
        ret = SortedDict()

        # Get the explicitly declared fields
        base_fields = copy.deepcopy(self.base_fields)
        for key, field in base_fields.items():
            ret[key] = field

        # Add in the default fields
        default_fields = self.get_default_fields()
        for key, val in default_fields.items():
            if key not in ret:
                ret[key] = val

        # If 'fields' is specified, use those fields, in that order.
        if self.opts.fields:
            assert isinstance(self.opts.fields, (list, tuple)), '`fields` must be a list or tuple'
            new = SortedDict()
            for key in self.opts.fields:
                new[key] = ret[key]
            ret = new

        # Remove anything in 'exclude'
        if self.opts.exclude:
            assert isinstance(self.opts.exclude, (list, tuple)), '`exclude` must be a list or tuple'
            for key in self.opts.exclude:
                ret.pop(key, None)

        for key, field in ret.items():
            field.initialize(parent=self, field_name=key)

        return ret

    #####
    # Methods to convert or revert from objects <--> primitive representations.

    def get_field_key(self, field_name):
        """
        Return the key that should be used for a given field.
        """
        return field_name

    def restore_fields(self, data, files):
        """
        Core of deserialization, together with `restore_object`.
        Converts a dictionary of data into a dictionary of deserialized fields.
        """
        reverted_data = {}

        if data is not None and not isinstance(data, dict):
            self._errors['non_field_errors'] = ['Invalid data']
            return None

        for field_name, field in self.fields.items():
            field.initialize(parent=self, field_name=field_name)
            try:
                field.field_from_native(data, files, field_name, reverted_data)
            except ValidationError as err:
                self._errors[field_name] = list(err.messages)

        return reverted_data

    def perform_validation(self, attrs):
        """
        Run `validate_<fieldname>()` and `validate()` methods on the serializer
        """
        for field_name, field in self.fields.items():
            if field_name in self._errors:
                continue
            try:
                validate_method = getattr(self, 'validate_%s' % field_name, None)
                if validate_method:
                    source = field.source or field_name
                    attrs = validate_method(attrs, source)
            except ValidationError as err:
                self._errors[field_name] = self._errors.get(field_name, []) + list(err.messages)

        # If there are already errors, we don't run .validate() because
        # field-validation failed and thus `attrs` may not be complete.
        # which in turn can cause inconsistent validation errors.
        if not self._errors:
            try:
                attrs = self.validate(attrs)
            except ValidationError as err:
                if hasattr(err, 'message_dict'):
                    for field_name, error_messages in err.message_dict.items():
                        self._errors[field_name] = self._errors.get(field_name, []) + list(error_messages)
                elif hasattr(err, 'messages'):
                    self._errors['non_field_errors'] = err.messages

        return attrs

    def validate(self, attrs):
        """
        Stub method, to be overridden in Serializer subclasses
        """
        return attrs

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
        Serialize objects -> primitives.
        """
        ret = self._dict_class()
        ret.fields = {}

        for field_name, field in self.fields.items():
            field.initialize(parent=self, field_name=field_name)
            key = self.get_field_key(field_name)
            value = field.field_to_native(obj, field_name)
            ret[key] = value
            ret.fields[key] = field
        return ret

    def from_native(self, data, files):
        """
        Deserialize primitives -> objects.
        """
        self._errors = {}
        if data is not None or files is not None:
            attrs = self.restore_fields(data, files)
            if attrs is not None:
                attrs = self.perform_validation(attrs)
        else:
            self._errors['non_field_errors'] = ['No input provided']

        if not self._errors:
            return self.restore_object(attrs, instance=getattr(self, 'object', None))

    def field_to_native(self, obj, field_name):
        """
        Override default so that the serializer can be used as a nested field
        across relationships.
        """
        if self.source == '*':
            return self.to_native(obj)

        try:
            source = self.source or field_name
            value = obj

            for component in source.split('.'):
                value = get_component(value, component)
                if value is None:
                    break
        except ObjectDoesNotExist:
            return None

        if is_simple_callable(getattr(value, 'all', None)):
            return [self.to_native(item) for item in value.all()]

        if value is None:
            return None

        if self.many is not None:
            many = self.many
        else:
            many = hasattr(value, '__iter__') and not isinstance(value, (Page, dict, six.text_type))

        if many:
            return [self.to_native(item) for item in value]
        return self.to_native(value)

    def field_from_native(self, data, files, field_name, into):
        """
        Override default so that the serializer can be used as a writable
        nested field across relationships.
        """
        if self.read_only:
            return

        try:
            value = data[field_name]
        except KeyError:
            if self.default is not None and not self.partial:
                # Note: partial updates shouldn't set defaults
                value = copy.deepcopy(self.default)
            else:
                if self.required:
                    raise ValidationError(self.error_messages['required'])
                return

        # Set the serializer object if it exists
        obj = getattr(self.parent.object, field_name) if self.parent.object else None

        if self.source == '*':
            if value:
                into.update(value)
        else:
            if value in (None, ''):
                into[(self.source or field_name)] = None
            else:
                kwargs = {
                    'instance': obj,
                    'data': value,
                    'context': self.context,
                    'partial': self.partial,
                    'many': self.many
                }
                serializer = self.__class__(**kwargs)

                if serializer.is_valid():
                    into[self.source or field_name] = serializer.object
                else:
                    # Propagate errors up to our parent
                    raise NestedValidationError(serializer.errors)

    def get_identity(self, data):
        """
        This hook is required for bulk update.
        It is used to determine the canonical identity of a given object.

        Note that the data has not been validated at this point, so we need
        to make sure that we catch any cases of incorrect datatypes being
        passed to this method.
        """
        try:
            return data.get('id', None)
        except AttributeError:
            return None

    @property
    def errors(self):
        """
        Run deserialization and return error data,
        setting self.object if no errors occurred.
        """
        if self._errors is None:
            data, files = self.init_data, self.init_files

            if self.many is not None:
                many = self.many
            else:
                many = hasattr(data, '__iter__') and not isinstance(data, (Page, dict, six.text_type))
                if many:
                    warnings.warn('Implict list/queryset serialization is deprecated. '
                                  'Use the `many=True` flag when instantiating the serializer.',
                                  DeprecationWarning, stacklevel=3)

            if many:
                ret = []
                errors = []
                update = self.object is not None

                if update:
                    # If this is a bulk update we need to map all the objects
                    # to a canonical identity so we can determine which
                    # individual object is being updated for each item in the
                    # incoming data
                    objects = self.object
                    identities = [self.get_identity(self.to_native(obj)) for obj in objects]
                    identity_to_objects = dict(zip(identities, objects))

                if hasattr(data, '__iter__') and not isinstance(data, (dict, six.text_type)):
                    for item in data:
                        if update:
                            # Determine which object we're updating
                            identity = self.get_identity(item)
                            self.object = identity_to_objects.pop(identity, None)
                            if self.object is None and not self.allow_add_remove:
                                ret.append(None)
                                errors.append({'non_field_errors': ['Cannot create a new item, only existing items may be updated.']})
                                continue

                        ret.append(self.from_native(item, None))
                        errors.append(self._errors)

                    if update:
                        self._deleted = identity_to_objects.values()

                    self._errors = any(errors) and errors or []
                else:
                    self._errors = {'non_field_errors': ['Expected a list of items.']}
            else:
                ret = self.from_native(data, files)

            if not self._errors:
                self.object = ret

        return self._errors

    def is_valid(self):
        return not self.errors

    @property
    def data(self):
        """
        Returns the serialized data on the serializer.
        """
        if self._data is None:
            obj = self.object

            if self.many is not None:
                many = self.many
            else:
                many = hasattr(obj, '__iter__') and not isinstance(obj, (Page, dict))
                if many:
                    warnings.warn('Implict list/queryset serialization is deprecated. '
                                  'Use the `many=True` flag when instantiating the serializer.',
                                  DeprecationWarning, stacklevel=2)

            if many:
                self._data = [self.to_native(item) for item in obj]
            else:
                self._data = self.to_native(obj)

        return self._data

    def save_object(self, obj, **kwargs):
        obj.save(**kwargs)

    def delete_object(self, obj):
        obj.delete()

    def save(self, **kwargs):
        """
        Save the deserialized object and return it.
        """
        if isinstance(self.object, list):
            [self.save_object(item, **kwargs) for item in self.object]
        else:
            self.save_object(self.object, **kwargs)

        if self.allow_add_remove and self._deleted:
            [self.delete_object(item) for item in self._deleted]

        return self.object

    def metadata(self):
        """
        Return a dictionary of metadata about the fields on the serializer.
        Useful for things like responding to OPTIONS requests, or generating
        API schemas for auto-documentation.
        """
        return SortedDict(
            [(field_name, field.metadata())
            for field_name, field in six.iteritems(self.fields)]
        )


class Serializer(six.with_metaclass(SerializerMetaclass, BaseSerializer)):
    pass


class ModelSerializerOptions(SerializerOptions):
    """
    Meta class options for ModelSerializer
    """
    def __init__(self, meta):
        super(ModelSerializerOptions, self).__init__(meta)
        self.model = getattr(meta, 'model', None)
        self.read_only_fields = getattr(meta, 'read_only_fields', ())


class ModelSerializer(Serializer):
    """
    A serializer that deals with model instances and querysets.
    """
    _options_class = ModelSerializerOptions

    field_mapping = {
        models.AutoField: IntegerField,
        models.FloatField: FloatField,
        models.IntegerField: IntegerField,
        models.PositiveIntegerField: IntegerField,
        models.SmallIntegerField: IntegerField,
        models.PositiveSmallIntegerField: IntegerField,
        models.DateTimeField: DateTimeField,
        models.DateField: DateField,
        models.TimeField: TimeField,
        models.DecimalField: DecimalField,
        models.EmailField: EmailField,
        models.CharField: CharField,
        models.URLField: URLField,
        models.SlugField: SlugField,
        models.TextField: CharField,
        models.CommaSeparatedIntegerField: CharField,
        models.BooleanField: BooleanField,
        models.FileField: FileField,
        models.ImageField: ImageField,
    }

    def get_default_fields(self):
        """
        Return all the fields that should be serialized for the model.
        """

        cls = self.opts.model
        assert cls is not None, \
                "Serializer class '%s' is missing 'model' Meta option" % self.__class__.__name__
        opts = get_concrete_model(cls)._meta
        ret = SortedDict()
        nested = bool(self.opts.depth)

        # Deal with adding the primary key field
        pk_field = opts.pk
        while pk_field.rel and pk_field.rel.parent_link:
            # If model is a child via multitable inheritance, use parent's pk
            pk_field = pk_field.rel.to._meta.pk

        field = self.get_pk_field(pk_field)
        if field:
            ret[pk_field.name] = field

        # Deal with forward relationships
        forward_rels = [field for field in opts.fields if field.serialize]
        forward_rels += [field for field in opts.many_to_many if field.serialize]

        for model_field in forward_rels:
            has_through_model = False

            if model_field.rel:
                to_many = isinstance(model_field,
                                     models.fields.related.ManyToManyField)
                related_model = model_field.rel.to

                if to_many and not model_field.rel.through._meta.auto_created:
                    has_through_model = True

            if model_field.rel and nested:
                if len(inspect.getargspec(self.get_nested_field).args) == 2:
                    warnings.warn(
                        'The `get_nested_field(model_field)` call signature '
                        'is due to be deprecated. '
                        'Use `get_nested_field(model_field, related_model, '
                        'to_many) instead',
                        PendingDeprecationWarning
                    )
                    field = self.get_nested_field(model_field)
                else:
                    field = self.get_nested_field(model_field, related_model, to_many)
            elif model_field.rel:
                if len(inspect.getargspec(self.get_nested_field).args) == 3:
                    warnings.warn(
                        'The `get_related_field(model_field, to_many)` call '
                        'signature is due to be deprecated. '
                        'Use `get_related_field(model_field, related_model, '
                        'to_many) instead',
                        PendingDeprecationWarning
                    )
                    field = self.get_related_field(model_field, to_many=to_many)
                else:
                    field = self.get_related_field(model_field, related_model, to_many)
            else:
                field = self.get_field(model_field)

            if field:
                if has_through_model:
                    field.read_only = True

                ret[model_field.name] = field

        # Deal with reverse relationships
        if not self.opts.fields:
            reverse_rels = []
        else:
            # Reverse relationships are only included if they are explicitly
            # present in the `fields` option on the serializer
            reverse_rels = opts.get_all_related_objects()
            reverse_rels += opts.get_all_related_many_to_many_objects()

        for relation in reverse_rels:
            accessor_name = relation.get_accessor_name()
            if not self.opts.fields or accessor_name not in self.opts.fields:
                continue
            related_model = relation.model
            to_many = relation.field.rel.multiple
            has_through_model = False
            is_m2m = isinstance(relation.field,
                                models.fields.related.ManyToManyField)

            if is_m2m and not relation.field.rel.through._meta.auto_created:
                has_through_model = True

            if nested:
                field = self.get_nested_field(None, related_model, to_many)
            else:
                field = self.get_related_field(None, related_model, to_many)

            if field:
                if has_through_model:
                    field.read_only = True

                ret[accessor_name] = field

        # Add the `read_only` flag to any fields that have bee specified
        # in the `read_only_fields` option
        for field_name in self.opts.read_only_fields:
            assert field_name not in self.base_fields.keys(), \
                "field '%s' on serializer '%s' specfied in " \
                "`read_only_fields`, but also added " \
                "as an explict field.  Remove it from `read_only_fields`." % \
                (field_name, self.__class__.__name__)
            assert field_name in ret, \
                "Noexistant field '%s' specified in `read_only_fields` " \
                "on serializer '%s'." % \
                (self.__class__.__name__, field_name)
            ret[field_name].read_only = True

        return ret

    def get_pk_field(self, model_field):
        """
        Returns a default instance of the pk field.
        """
        return self.get_field(model_field)

    def get_nested_field(self, model_field, related_model, to_many):
        """
        Creates a default instance of a nested relational field.

        Note that model_field will be `None` for reverse relationships.
        """
        class NestedModelSerializer(ModelSerializer):
            class Meta:
                model = related_model
                depth = self.opts.depth - 1

        return NestedModelSerializer(many=to_many)

    def get_related_field(self, model_field, related_model, to_many):
        """
        Creates a default instance of a flat relational field.

        Note that model_field will be `None` for reverse relationships.
        """
        # TODO: filter queryset using:
        # .using(db).complex_filter(self.rel.limit_choices_to)

        kwargs = {
            'queryset': related_model._default_manager,
            'many': to_many
        }

        if model_field:
            kwargs['required'] = not(model_field.null or model_field.blank)

        return PrimaryKeyRelatedField(**kwargs)

    def get_field(self, model_field):
        """
        Creates a default instance of a basic non-relational field.
        """
        kwargs = {}

        if model_field.null or model_field.blank:
            kwargs['required'] = False

        if isinstance(model_field, models.AutoField) or not model_field.editable:
            kwargs['read_only'] = True

        if model_field.has_default():
            kwargs['default'] = model_field.get_default()

        if issubclass(model_field.__class__, models.TextField):
            kwargs['widget'] = widgets.Textarea

        if model_field.verbose_name is not None:
            kwargs['label'] = model_field.verbose_name

        if model_field.help_text is not None:
            kwargs['help_text'] = model_field.help_text

        # TODO: TypedChoiceField?
        if model_field.flatchoices:  # This ModelField contains choices
            kwargs['choices'] = model_field.flatchoices
            return ChoiceField(**kwargs)

        # put this below the ChoiceField because min_value isn't a valid initializer
        if issubclass(model_field.__class__, models.PositiveIntegerField) or\
                issubclass(model_field.__class__, models.PositiveSmallIntegerField):
            kwargs['min_value'] = 0

        attribute_dict = {
            models.CharField: ['max_length'],
            models.CommaSeparatedIntegerField: ['max_length'],
            models.DecimalField: ['max_digits', 'decimal_places'],
            models.EmailField: ['max_length'],
            models.FileField: ['max_length'],
            models.ImageField: ['max_length'],
            models.SlugField: ['max_length'],
            models.URLField: ['max_length'],
        }

        if model_field.__class__ in attribute_dict:
            attributes = attribute_dict[model_field.__class__]
            for attribute in attributes:
                kwargs.update({attribute: getattr(model_field, attribute)})

        try:
            return self.field_mapping[model_field.__class__](**kwargs)
        except KeyError:
            return ModelField(model_field=model_field, **kwargs)

    def get_validation_exclusions(self):
        """
        Return a list of field names to exclude from model validation.
        """
        cls = self.opts.model
        opts = get_concrete_model(cls)._meta
        exclusions = [field.name for field in opts.fields + opts.many_to_many]
        for field_name, field in self.fields.items():
            field_name = field.source or field_name
            if field_name in exclusions and not field.read_only:
                exclusions.remove(field_name)
        return exclusions

    def full_clean(self, instance):
        """
        Perform Django's full_clean, and populate the `errors` dictionary
        if any validation errors occur.

        Note that we don't perform this inside the `.restore_object()` method,
        so that subclasses can override `.restore_object()`, and still get
        the full_clean validation checking.
        """
        try:
            instance.full_clean(exclude=self.get_validation_exclusions())
        except ValidationError as err:
            self._errors = err.message_dict
            return None
        return instance

    def restore_object(self, attrs, instance=None):
        """
        Restore the model instance.
        """
        m2m_data = {}
        related_data = {}
        meta = self.opts.model._meta

        # Reverse fk or one-to-one relations
        for (obj, model) in meta.get_all_related_objects_with_model():
            field_name = obj.field.related_query_name()
            if field_name in attrs:
                related_data[field_name] = attrs.pop(field_name)

        # Reverse m2m relations
        for (obj, model) in meta.get_all_related_m2m_objects_with_model():
            field_name = obj.field.related_query_name()
            if field_name in attrs:
                m2m_data[field_name] = attrs.pop(field_name)

        # Forward m2m relations
        for field in meta.many_to_many:
            if field.name in attrs:
                m2m_data[field.name] = attrs.pop(field.name)

        # Update an existing instance...
        if instance is not None:
            for key, val in attrs.items():
                setattr(instance, key, val)

        # ...or create a new instance
        else:
            instance = self.opts.model(**attrs)

        # Any relations that cannot be set until we've
        # saved the model get hidden away on these
        # private attributes, so we can deal with them
        # at the point of save.
        instance._related_data = related_data
        instance._m2m_data = m2m_data

        return instance

    def from_native(self, data, files):
        """
        Override the default method to also include model field validation.
        """
        instance = super(ModelSerializer, self).from_native(data, files)
        if not self._errors:
            return self.full_clean(instance)

    def save_object(self, obj, **kwargs):
        """
        Save the deserialized object and return it.
        """
        obj.save(**kwargs)

        if getattr(obj, '_m2m_data', None):
            for accessor_name, object_list in obj._m2m_data.items():
                setattr(obj, accessor_name, object_list)
            del(obj._m2m_data)

        if getattr(obj, '_related_data', None):
            for accessor_name, related in obj._related_data.items():
                setattr(obj, accessor_name, related)
            del(obj._related_data)


class HyperlinkedModelSerializerOptions(ModelSerializerOptions):
    """
    Options for HyperlinkedModelSerializer
    """
    def __init__(self, meta):
        super(HyperlinkedModelSerializerOptions, self).__init__(meta)
        self.view_name = getattr(meta, 'view_name', None)
        self.lookup_field = getattr(meta, 'lookup_field', None)


class HyperlinkedModelSerializer(ModelSerializer):
    """
    A subclass of ModelSerializer that uses hyperlinked relationships,
    instead of primary key relationships.
    """
    _options_class = HyperlinkedModelSerializerOptions
    _default_view_name = '%(model_name)s-detail'
    _hyperlink_field_class = HyperlinkedRelatedField

    # Just a placeholder to ensure 'url' is the first field
    # The field itself is actually created on initialization,
    # when the view_name and lookup_field arguments are available.
    url = Field()

    def __init__(self, *args, **kwargs):
        super(HyperlinkedModelSerializer, self).__init__(*args, **kwargs)

        if self.opts.view_name is None:
            self.opts.view_name = self._get_default_view_name(self.opts.model)

        url_field = HyperlinkedIdentityField(
            view_name=self.opts.view_name,
            lookup_field=self.opts.lookup_field
        )
        url_field.initialize(self, 'url')
        self.fields['url'] = url_field

    def _get_default_view_name(self, model):
        """
        Return the view name to use if 'view_name' is not specified in 'Meta'
        """
        model_meta = model._meta
        format_kwargs = {
            'app_label': model_meta.app_label,
            'model_name': model_meta.object_name.lower()
        }
        return self._default_view_name % format_kwargs

    def get_pk_field(self, model_field):
        if self.opts.fields and model_field.name in self.opts.fields:
            return self.get_field(model_field)

    def get_related_field(self, model_field, related_model, to_many):
        """
        Creates a default instance of a flat relational field.
        """
        # TODO: filter queryset using:
        # .using(db).complex_filter(self.rel.limit_choices_to)
        kwargs = {
            'queryset': related_model._default_manager,
            'view_name': self._get_default_view_name(related_model),
            'many': to_many
        }

        if model_field:
            kwargs['required'] = not(model_field.null or model_field.blank)

        if self.opts.lookup_field:
            kwargs['lookup_field'] = self.opts.lookup_field

        return self._hyperlink_field_class(**kwargs)

    def get_identity(self, data):
        """
        This hook is required for bulk update.
        We need to override the default, to use the url as the identity.
        """
        try:
            return data.get('url', None)
        except AttributeError:
            return None
