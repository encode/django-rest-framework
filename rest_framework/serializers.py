"""
Serializers and ModelSerializers are similar to Forms and ModelForms.
Unlike forms, they are not constrained to dealing with HTML output, and
form encoded input.

Serialization in REST framework is a two-phase process:

1. Serializers marshal between complex types like model instances, and
python primitives.
2. The process of marshalling between python primitives and request and
response content is handled by parsers and renderers.
"""
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import six
from django.utils.datastructures import SortedDict
from collections import namedtuple
from rest_framework.compat import clean_manytomany_helptext
from rest_framework.fields import empty, set_value, Field, SkipField
from rest_framework.settings import api_settings
from rest_framework.utils import html, modelinfo, representation
import copy

# Note: We do the following so that users of the framework can use this style:
#
#     example_field = serializers.CharField(...)
#
# This helps keep the separation between model fields, form fields, and
# serializer fields more explicit.

from rest_framework.relations import *  # NOQA
from rest_framework.fields import *  # NOQA


FieldResult = namedtuple('FieldResult', ['field', 'value', 'error'])


class BaseSerializer(Field):
    """
    The BaseSerializer class provides a minimal class which may be used
    for writing custom serializer implementations.
    """

    def __init__(self, instance=None, data=None, **kwargs):
        super(BaseSerializer, self).__init__(**kwargs)
        self.instance = instance
        self._initial_data = data

    def to_native(self, data):
        raise NotImplementedError('`to_native()` must be implemented.')

    def to_primative(self, instance):
        raise NotImplementedError('`to_primative()` must be implemented.')

    def update(self, instance, attrs):
        raise NotImplementedError('`update()` must be implemented.')

    def create(self, attrs):
        raise NotImplementedError('`create()` must be implemented.')

    def save(self, extras=None):
        attrs = self.validated_data
        if extras is not None:
            attrs = dict(list(attrs.items()) + list(extras.items()))

        if self.instance is not None:
            self.update(self.instance, attrs)
        else:
            self.instance = self.create(attrs)

        return self.instance

    def is_valid(self, raise_exception=False):
        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.to_native(self._initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.message_dict
            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise ValidationError(self._errors)

        return not bool(self._errors)

    @property
    def data(self):
        if not hasattr(self, '_data'):
            if self.instance is not None:
                self._data = self.to_primative(self.instance)
            elif self._initial_data is not None:
                self._data = dict([
                    (field_name, field.get_value(self._initial_data))
                    for field_name, field in self.fields.items()
                ])
            else:
                self._data = self.get_initial()
        return self._data

    @property
    def errors(self):
        if not hasattr(self, '_errors'):
            msg = 'You must call `.is_valid()` before accessing `.errors`.'
            raise AssertionError(msg)
        return self._errors

    @property
    def validated_data(self):
        if not hasattr(self, '_validated_data'):
            msg = 'You must call `.is_valid()` before accessing `.validated_data`.'
            raise AssertionError(msg)
        return self._validated_data


class SerializerMetaclass(type):
    """
    This metaclass sets a dictionary named `base_fields` on the class.

    Any instances of `Field` included as attributes on either the class
    or on any of its superclasses will be include in the
    `base_fields` dictionary.
    """

    @classmethod
    def _get_fields(cls, bases, attrs):
        fields = [(field_name, attrs.pop(field_name))
                  for field_name, obj in list(attrs.items())
                  if isinstance(obj, Field)]
        fields.sort(key=lambda x: x[1]._creation_counter)

        # If this class is subclassing another Serializer, add that Serializer's
        # fields.  Note that we loop over the bases in *reverse*. This is necessary
        # in order to maintain the correct order of fields.
        for base in bases[::-1]:
            if hasattr(base, 'base_fields'):
                fields = list(base.base_fields.items()) + fields

        return SortedDict(fields)

    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = cls._get_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(SerializerMetaclass)
class Serializer(BaseSerializer):

    def __new__(cls, *args, **kwargs):
        if kwargs.pop('many', False):
            kwargs['child'] = cls()
            return ListSerializer(*args, **kwargs)
        return super(Serializer, cls).__new__(cls, *args, **kwargs)

    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', {})
        kwargs.pop('partial', None)
        kwargs.pop('many', False)

        super(Serializer, self).__init__(*args, **kwargs)

        # Every new serializer is created with a clone of the field instances.
        # This allows users to dynamically modify the fields on a serializer
        # instance without affecting every other serializer class.
        self.fields = self.get_fields()

        # Setup all the child fields, to provide them with the current context.
        for field_name, field in self.fields.items():
            field.bind(field_name, self, self)

    def get_fields(self):
        return copy.deepcopy(self.base_fields)

    def bind(self, field_name, parent, root):
        # If the serializer is used as a field then when it becomes bound
        # it also needs to bind all its child fields.
        super(Serializer, self).bind(field_name, parent, root)
        for field_name, field in self.fields.items():
            field.bind(field_name, self, root)

    def get_initial(self):
        return dict([
            (field.field_name, field.get_initial())
            for field in self.fields.values()
        ])

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # nested HTML forms.
        if html.is_html_input(dictionary):
            return html.parse_html_dict(dictionary, prefix=self.field_name)
        return dictionary.get(self.field_name, empty)

    def to_native(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        if not isinstance(data, dict):
            raise ValidationError({'non_field_errors': ['Invalid data']})

        ret = {}
        errors = {}
        fields = [field for field in self.fields.values() if not field.read_only]

        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.validate_value(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[field.field_name] = exc.messages
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise ValidationError(errors)

        try:
            return self.validate(ret)
        except ValidationError as exc:
            raise ValidationError({'non_field_errors': exc.messages})

    def to_primative(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = SortedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            native_value = field.get_attribute(instance)
            ret[field.field_name] = field.to_primative(native_value)

        return ret

    def validate(self, attrs):
        return attrs

    def __iter__(self):
        errors = self.errors if hasattr(self, '_errors') else {}
        for field in self.fields.values():
            value = self.data.get(field.field_name) if self.data else None
            error = errors.get(field.field_name)
            yield FieldResult(field, value, error)

    def __repr__(self):
        return representation.serializer_repr(self, indent=1)


class ListSerializer(BaseSerializer):
    child = None
    initial = []

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert self.child is not None, '`child` is a required argument.'
        self.context = kwargs.pop('context', {})
        kwargs.pop('partial', None)

        super(ListSerializer, self).__init__(*args, **kwargs)
        self.child.bind('', self, self)

    def bind(self, field_name, parent, root):
        # If the list is used as a field then it needs to provide
        # the current context to the child serializer.
        super(ListSerializer, self).bind(field_name, parent, root)
        self.child.bind(field_name, self, root)

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # lists in HTML forms.
        if is_html_input(dictionary):
            return html.parse_html_list(dictionary, prefix=self.field_name)
        return dictionary.get(self.field_name, empty)

    def to_native(self, data):
        """
        List of dicts of native values <- List of dicts of primitive datatypes.
        """
        if html.is_html_input(data):
            data = html.parse_html_list(data)

        return [self.child.validate(item) for item in data]

    def to_primative(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [self.child.to_primative(item) for item in data]

    def create(self, attrs_list):
        return [self.child.create(attrs) for attrs in attrs_list]

    def save(self):
        if self.instance is not None:
            self.update(self.instance, self.validated_data)
        self.instance = self.create(self.validated_data)
        return self.instance

    def __repr__(self):
        return representation.list_repr(self, indent=1)


class ModelSerializerOptions(object):
    """
    Meta class options for ModelSerializer
    """
    def __init__(self, meta):
        self.model = getattr(meta, 'model')
        self.fields = getattr(meta, 'fields', ())
        self.depth = getattr(meta, 'depth', 0)


def lookup_class(mapping, obj):
    """
    Takes a dictionary with classes as keys, and an object.
    Traverses the object's inheritance hierarchy in method
    resolution order, and returns the first matching value
    from the dictionary or None.
    """
    return next(
        (mapping[cls] for cls in inspect.getmro(obj.__class__) if cls in mapping),
        None
    )


class ModelSerializer(Serializer):
    field_mapping = {
        models.AutoField: IntegerField,
        models.BigIntegerField: IntegerField,
        models.BooleanField: BooleanField,
        models.CharField: CharField,
        models.CommaSeparatedIntegerField: CharField,
        models.DateField: DateField,
        models.DateTimeField: DateTimeField,
        models.DecimalField: DecimalField,
        models.EmailField: EmailField,
        models.FileField: FileField,
        models.FloatField: FloatField,
        models.ImageField: ImageField,
        models.IntegerField: IntegerField,
        models.NullBooleanField: BooleanField,
        models.PositiveIntegerField: IntegerField,
        models.PositiveSmallIntegerField: IntegerField,
        models.SlugField: SlugField,
        models.SmallIntegerField: IntegerField,
        models.TextField: CharField,
        models.TimeField: TimeField,
        models.URLField: URLField,
    }

    _options_class = ModelSerializerOptions

    def __init__(self, *args, **kwargs):
        self.opts = self._options_class(self.Meta)
        super(ModelSerializer, self).__init__(*args, **kwargs)

    def create(self, attrs):
        ModelClass = self.opts.model
        return ModelClass.objects.create(**attrs)

    def update(self, obj, attrs):
        for attr, value in attrs.items():
            setattr(obj, attr, value)
        obj.save()

    def get_fields(self):
        # Get the explicitly declared fields.
        fields = copy.deepcopy(self.base_fields)

        # Add in the default fields.
        for key, val in self.get_default_fields().items():
            if key not in fields:
                fields[key] = val

        # If `fields` is set on the `Meta` class,
        # then use only those fields, and in that order.
        if self.opts.fields:
            fields = SortedDict([
                (key, fields[key]) for key in self.opts.fields
            ])

        return fields

    def get_default_fields(self):
        """
        Return all the fields that should be serialized for the model.
        """
        info = modelinfo.get_field_info(self.opts.model)
        ret = SortedDict()

        serializer_url_field = self.get_url_field()
        if serializer_url_field:
            ret[api_settings.URL_FIELD_NAME] = serializer_url_field

        serializer_pk_field = self.get_pk_field(info.pk)
        if serializer_pk_field:
            ret[info.pk.name] = serializer_pk_field

        # Regular fields
        for field_name, field in info.fields.items():
            ret[field_name] = self.get_field(field)

        # Forward relations
        for field_name, relation_info in info.forward_relations.items():
            if self.opts.depth:
                ret[field_name] = self.get_nested_field(*relation_info)
            else:
                ret[field_name] = self.get_related_field(*relation_info)

        # Reverse relations
        for accessor_name, relation_info in info.reverse_relations.items():
            if accessor_name in self.opts.fields:
                if self.opts.depth:
                    ret[field_name] = self.get_nested_field(*relation_info)
                else:
                    ret[field_name] = self.get_related_field(*relation_info)

        return ret

    def get_url_field(self):
        return None

    def get_pk_field(self, model_field):
        """
        Returns a default instance of the pk field.
        """
        return self.get_field(model_field)

    def get_nested_field(self, model_field, related_model, to_many, has_through_model):
        """
        Creates a default instance of a nested relational field.

        Note that model_field will be `None` for reverse relationships.
        """
        class NestedModelSerializer(ModelSerializer):
            class Meta:
                model = related_model
                depth = self.opts.depth - 1

        kwargs = {'read_only': True}
        if to_many:
            kwargs['many'] = True
        return NestedModelSerializer(**kwargs)

    def get_related_field(self, model_field, related_model, to_many, has_through_model):
        """
        Creates a default instance of a flat relational field.

        Note that model_field will be `None` for reverse relationships.
        """
        kwargs = {
            'queryset': related_model._default_manager,
        }

        if to_many:
            kwargs['many'] = True

        if has_through_model:
            kwargs['read_only'] = True
            kwargs.pop('queryset', None)

        if model_field:
            if model_field.null or model_field.blank:
                kwargs['required'] = False
            if model_field.verbose_name:
                kwargs['label'] = model_field.verbose_name
            if not model_field.editable:
                kwargs['read_only'] = True
                kwargs.pop('queryset', None)
            help_text = clean_manytomany_helptext(model_field.help_text)
            if help_text:
                kwargs['help_text'] = help_text

        return PrimaryKeyRelatedField(**kwargs)

    def get_field(self, model_field):
        """
        Creates a default instance of a basic non-relational field.
        """
        kwargs = {}
        validator_kwarg = model_field.validators

        if model_field.null or model_field.blank:
            kwargs['required'] = False

        if model_field.verbose_name is not None:
            kwargs['label'] = model_field.verbose_name

        if model_field.help_text:
            kwargs['help_text'] = model_field.help_text

        if isinstance(model_field, models.AutoField) or not model_field.editable:
            kwargs['read_only'] = True
            # Read only implies that the field is not required.
            # We have a cleaner repr on the instance if we don't set it.
            kwargs.pop('required', None)

        if model_field.has_default():
            kwargs['default'] = model_field.get_default()
            # Having a default implies that the field is not required.
            # We have a cleaner repr on the instance if we don't set it.
            kwargs.pop('required', None)

        if model_field.flatchoices:
            # If this model field contains choices, then use a ChoiceField,
            # rather than the standard serializer field for this type.
            # Note that we return this prior to setting any validation type
            # keyword arguments, as those are not valid initializers.
            kwargs['choices'] = model_field.flatchoices
            return ChoiceField(**kwargs)

        # Ensure that max_length is passed explicitly as a keyword arg,
        # rather than as a validator.
        max_length = getattr(model_field, 'max_length', None)
        if max_length is not None:
            kwargs['max_length'] = max_length
            validator_kwarg = [
                validator for validator in validator_kwarg
                if not isinstance(validator, validators.MaxLengthValidator)
            ]

        # Ensure that min_length is passed explicitly as a keyword arg,
        # rather than as a validator.
        min_length = getattr(model_field, 'min_length', None)
        if min_length is not None:
            kwargs['min_length'] = min_length
            validator_kwarg = [
                validator for validator in validator_kwarg
                if not isinstance(validator, validators.MinLengthValidator)
            ]

        # Ensure that max_value is passed explicitly as a keyword arg,
        # rather than as a validator.
        max_value = next((
            validator.limit_value for validator in validator_kwarg
            if isinstance(validator, validators.MaxValueValidator)
        ), None)
        if max_value is not None:
            kwargs['max_value'] = max_value
            validator_kwarg = [
                validator for validator in validator_kwarg
                if not isinstance(validator, validators.MaxValueValidator)
            ]

        # Ensure that max_value is passed explicitly as a keyword arg,
        # rather than as a validator.
        min_value = next((
            validator.limit_value for validator in validator_kwarg
            if isinstance(validator, validators.MinValueValidator)
        ), None)
        if min_value is not None:
            kwargs['min_value'] = min_value
            validator_kwarg = [
                validator for validator in validator_kwarg
                if not isinstance(validator, validators.MinValueValidator)
            ]

        # URLField does not need to include the URLValidator argument,
        # as it is explicitly added in.
        if isinstance(model_field, models.URLField):
            validator_kwarg = [
                validator for validator in validator_kwarg
                if not isinstance(validator, validators.URLValidator)
            ]

        # EmailField does not need to include the validate_email argument,
        # as it is explicitly added in.
        if isinstance(model_field, models.EmailField):
            validator_kwarg = [
                validator for validator in validator_kwarg
                if validator is not validators.validate_email
            ]

        # SlugField do not need to include the 'validate_slug' argument,
        if isinstance(model_field, models.SlugField):
            validator_kwarg = [
                validator for validator in validator_kwarg
                if validator is not validators.validate_slug
            ]

        max_digits = getattr(model_field, 'max_digits', None)
        if max_digits is not None:
            kwargs['max_digits'] = max_digits

        decimal_places = getattr(model_field, 'decimal_places', None)
        if decimal_places is not None:
            kwargs['decimal_places'] = decimal_places

        if isinstance(model_field, models.BooleanField):
            # models.BooleanField has `blank=True`, but *is* actually
            # required *unless* a default is provided.
            # Also note that <1.6 `default=False`, >=1.6 `default=None`.
            kwargs.pop('required', None)

        if validator_kwarg:
            kwargs['validators'] = validator_kwarg

        cls = lookup_class(self.field_mapping, model_field)
        if cls is None:
            cls = ModelField
            kwargs['model_field'] = model_field
        return cls(**kwargs)


class HyperlinkedModelSerializerOptions(ModelSerializerOptions):
    """
    Options for HyperlinkedModelSerializer
    """
    def __init__(self, meta):
        super(HyperlinkedModelSerializerOptions, self).__init__(meta)
        self.view_name = getattr(meta, 'view_name', None)
        self.lookup_field = getattr(meta, 'lookup_field', None)


class HyperlinkedModelSerializer(ModelSerializer):
    _options_class = HyperlinkedModelSerializerOptions

    def get_url_field(self):
        if self.opts.view_name is not None:
            view_name = self.opts.view_name
        else:
            view_name = self.get_default_view_name(self.opts.model)

        kwargs = {
            'view_name': view_name
        }
        if self.opts.lookup_field:
            kwargs['lookup_field'] = self.opts.lookup_field

        return HyperlinkedIdentityField(**kwargs)

    def get_pk_field(self, model_field):
        if self.opts.fields and model_field.name in self.opts.fields:
            return self.get_field(model_field)

    def get_related_field(self, model_field, related_model, to_many, has_through_model):
        """
        Creates a default instance of a flat relational field.
        """
        kwargs = {
            'queryset': related_model._default_manager,
            'view_name': self.get_default_view_name(related_model),
        }

        if to_many:
            kwargs['many'] = True

        if has_through_model:
            kwargs['read_only'] = True
            kwargs.pop('queryset', None)

        if model_field:
            if model_field.null or model_field.blank:
                kwargs['required'] = False
            if model_field.verbose_name:
                kwargs['label'] = model_field.verbose_name
            if not model_field.editable:
                kwargs['read_only'] = True
                kwargs.pop('queryset', None)
            help_text = clean_manytomany_helptext(model_field.help_text)
            if help_text:
                kwargs['help_text'] = help_text

        return HyperlinkedRelatedField(**kwargs)

    def get_default_view_name(self, model):
        """
        Return the view name to use for related models.
        """
        return '%(model_name)s-detail' % {
            'app_label': model._meta.app_label,
            'model_name': model._meta.object_name.lower()
        }
