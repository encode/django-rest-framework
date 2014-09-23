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
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models
from django.utils import six
from django.utils.datastructures import SortedDict
from collections import namedtuple
from rest_framework.fields import empty, set_value, Field, SkipField
from rest_framework.settings import api_settings
from rest_framework.utils import html, model_meta, representation
from rest_framework.utils.field_mapping import (
    get_url_kwargs, get_field_kwargs,
    get_relation_kwargs, get_nested_relation_kwargs,
    lookup_class
)
import copy
import inspect

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

    def to_internal_value(self, data):
        raise NotImplementedError('`to_internal_value()` must be implemented.')

    def to_representation(self, instance):
        raise NotImplementedError('`to_representation()` must be implemented.')

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
                self._validated_data = self.to_internal_value(self._initial_data)
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
                self._data = self.to_representation(self.instance)
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
    def _get_declared_fields(cls, bases, attrs):
        fields = [(field_name, attrs.pop(field_name))
                  for field_name, obj in list(attrs.items())
                  if isinstance(obj, Field)]
        fields.sort(key=lambda x: x[1]._creation_counter)

        # If this class is subclassing another Serializer, add that Serializer's
        # fields.  Note that we loop over the bases in *reverse*. This is necessary
        # in order to maintain the correct order of fields.
        for base in bases[::-1]:
            if hasattr(base, '_declared_fields'):
                fields = list(base._declared_fields.items()) + fields

        return SortedDict(fields)

    def __new__(cls, name, bases, attrs):
        attrs['_declared_fields'] = cls._get_declared_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(SerializerMetaclass)
class Serializer(BaseSerializer):
    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop('context', {})
        kwargs.pop('partial', None)
        kwargs.pop('many', None)

        super(Serializer, self).__init__(*args, **kwargs)

        # Every new serializer is created with a clone of the field instances.
        # This allows users to dynamically modify the fields on a serializer
        # instance without affecting every other serializer class.
        self.fields = self._get_base_fields()

        # Setup all the child fields, to provide them with the current context.
        for field_name, field in self.fields.items():
            field.bind(field_name, self, self)

    def __new__(cls, *args, **kwargs):
        # We override this method in order to automagically create
        # `ListSerializer` classes instead when `many=True` is set.
        if kwargs.pop('many', False):
            kwargs['child'] = cls()
            return ListSerializer(*args, **kwargs)
        return super(Serializer, cls).__new__(cls, *args, **kwargs)

    def _get_base_fields(self):
        return copy.deepcopy(self._declared_fields)

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

    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        if not isinstance(data, dict):
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: ['Invalid data']
            })

        ret = {}
        errors = {}
        fields = [field for field in self.fields.values() if not field.read_only]

        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
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
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: exc.messages
            })

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = SortedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            native_value = field.get_attribute(instance)
            ret[field.field_name] = field.to_representation(native_value)

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
        assert not inspect.isclass(self.child), '`child` has not been instantiated.'
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

    def to_internal_value(self, data):
        """
        List of dicts of native values <- List of dicts of primitive datatypes.
        """
        if html.is_html_input(data):
            data = html.parse_html_list(data)

        return [self.child.run_validation(item) for item in data]

    def to_representation(self, data):
        """
        List of object instances -> List of dicts of primitive datatypes.
        """
        return [self.child.to_representation(item) for item in data]

    def create(self, attrs_list):
        return [self.child.create(attrs) for attrs in attrs_list]

    def save(self):
        if self.instance is not None:
            self.update(self.instance, self.validated_data)
        self.instance = self.create(self.validated_data)
        return self.instance

    def __repr__(self):
        return representation.list_repr(self, indent=1)


class ModelSerializer(Serializer):
    _field_mapping = {
        models.AutoField: IntegerField,
        models.BigIntegerField: IntegerField,
        models.BooleanField: BooleanField,
        models.CharField: CharField,
        models.CommaSeparatedIntegerField: CharField,
        models.DateField: DateField,
        models.DateTimeField: DateTimeField,
        models.DecimalField: DecimalField,
        models.EmailField: EmailField,
        models.Field: ModelField,
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
    _related_class = PrimaryKeyRelatedField

    def create(self, attrs):
        ModelClass = self.Meta.model

        # Remove many-to-many relationships from attrs.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in attrs):
                many_to_many[field_name] = attrs.pop(field_name)

        instance = ModelClass.objects.create(**attrs)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                setattr(instance, field_name, value)

        return instance

    def update(self, obj, attrs):
        for attr, value in attrs.items():
            setattr(obj, attr, value)
        obj.save()

    def _get_base_fields(self):
        declared_fields = copy.deepcopy(self._declared_fields)

        ret = SortedDict()
        model = getattr(self.Meta, 'model')
        fields = getattr(self.Meta, 'fields', None)
        depth = getattr(self.Meta, 'depth', 0)
        extra_kwargs = getattr(self.Meta, 'extra_kwargs', {})

        # Retrieve metadata about fields & relationships on the model class.
        info = model_meta.get_field_info(model)

        # Use the default set of fields if none is supplied explicitly.
        if fields is None:
            fields = self._get_default_field_names(declared_fields, info)

        for field_name in fields:
            if field_name in declared_fields:
                # Field is explicitly declared on the class, use that.
                ret[field_name] = declared_fields[field_name]
                continue

            elif field_name == api_settings.URL_FIELD_NAME:
                # Create the URL field.
                field_cls = HyperlinkedIdentityField
                kwargs = get_url_kwargs(model)

            elif field_name in info.fields_and_pk:
                # Create regular model fields.
                model_field = info.fields_and_pk[field_name]
                field_cls = lookup_class(self._field_mapping, model_field)
                kwargs = get_field_kwargs(field_name, model_field)
                if 'choices' in kwargs:
                    # Fields with choices get coerced into `ChoiceField`
                    # instead of using their regular typed field.
                    field_cls = ChoiceField
                if not issubclass(field_cls, ModelField):
                    # `model_field` is only valid for the fallback case of
                    # `ModelField`, which is used when no other typed field
                    # matched to the model field.
                    kwargs.pop('model_field', None)

            elif field_name in info.relations:
                # Create forward and reverse relationships.
                relation_info = info.relations[field_name]
                if depth:
                    field_cls = self._get_nested_class(depth, relation_info)
                    kwargs = get_nested_relation_kwargs(relation_info)
                else:
                    field_cls = self._related_class
                    kwargs = get_relation_kwargs(field_name, relation_info)
                    # `view_name` is only valid for hyperlinked relationships.
                    if not issubclass(field_cls, HyperlinkedRelatedField):
                        kwargs.pop('view_name', None)

            elif hasattr(model, field_name):
                # Create a read only field for model methods and properties.
                field_cls = ReadOnlyField
                kwargs = {}

            else:
                raise ImproperlyConfigured(
                    'Field name `%s` is not valid for model `%s`.' %
                    (field_name, model.__class__.__name__)
                )

            # Check that any fields declared on the class are
            # also explicity included in `Meta.fields`.
            missing_fields = set(declared_fields.keys()) - set(fields)
            if missing_fields:
                missing_field = list(missing_fields)[0]
                raise ImproperlyConfigured(
                    'Field `%s` has been declared on serializer `%s`, but '
                    'is missing from `Meta.fields`.' %
                    (missing_field, self.__class__.__name__)
                )

            # Populate any kwargs defined in `Meta.extra_kwargs`
            kwargs.update(extra_kwargs.get(field_name, {}))

            # Create the serializer field.
            ret[field_name] = field_cls(**kwargs)

        return ret

    def _get_default_field_names(self, declared_fields, model_info):
        return (
            [model_info.pk.name] +
            list(declared_fields.keys()) +
            list(model_info.fields.keys()) +
            list(model_info.forward_relations.keys())
        )

    def _get_nested_class(self, nested_depth, relation_info):
        class NestedSerializer(ModelSerializer):
            class Meta:
                model = relation_info.related
                depth = nested_depth
        return NestedSerializer


class HyperlinkedModelSerializer(ModelSerializer):
    _related_class = HyperlinkedRelatedField

    def _get_default_field_names(self, declared_fields, model_info):
        return (
            [api_settings.URL_FIELD_NAME] +
            list(declared_fields.keys()) +
            list(model_info.fields.keys()) +
            list(model_info.forward_relations.keys())
        )

    def _get_nested_class(self, nested_depth, relation_info):
        class NestedSerializer(HyperlinkedModelSerializer):
            class Meta:
                model = relation_info.related
                depth = nested_depth
        return NestedSerializer
