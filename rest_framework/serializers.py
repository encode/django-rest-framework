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
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils import six
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty, set_value, Field, SkipField
from rest_framework.settings import api_settings
from rest_framework.utils import html, model_meta, representation
from rest_framework.utils.field_mapping import (
    get_url_kwargs, get_field_kwargs,
    get_relation_kwargs, get_nested_relation_kwargs,
    ClassLookupDict
)
from rest_framework.validators import (
    UniqueForDateValidator, UniqueForMonthValidator, UniqueForYearValidator,
    UniqueTogetherValidator
)
import copy
import inspect
import warnings

# Note: We do the following so that users of the framework can use this style:
#
#     example_field = serializers.CharField(...)
#
# This helps keep the separation between model fields, form fields, and
# serializer fields more explicit.

from rest_framework.relations import *  # NOQA
from rest_framework.fields import *  # NOQA


# BaseSerializer
# --------------

class BaseSerializer(Field):
    """
    The BaseSerializer class provides a minimal class which may be used
    for writing custom serializer implementations.
    """

    def __init__(self, instance=None, data=None, **kwargs):
        self.instance = instance
        self._initial_data = data
        self.partial = kwargs.pop('partial', False)
        self._context = kwargs.pop('context', {})
        kwargs.pop('many', None)
        super(BaseSerializer, self).__init__(**kwargs)

    def __new__(cls, *args, **kwargs):
        # We override this method in order to automagically create
        # `ListSerializer` classes instead when `many=True` is set.
        if kwargs.pop('many', False):
            kwargs['child'] = cls()
            return ListSerializer(*args, **kwargs)
        return super(BaseSerializer, cls).__new__(cls, *args, **kwargs)

    def to_internal_value(self, data):
        raise NotImplementedError('`to_internal_value()` must be implemented.')

    def to_representation(self, instance):
        raise NotImplementedError('`to_representation()` must be implemented.')

    def update(self, instance, validated_data):
        raise NotImplementedError('`update()` must be implemented.')

    def create(self, validated_data):
        raise NotImplementedError('`create()` must be implemented.')

    def save(self, **kwargs):
        validated_data = self.validated_data
        if kwargs:
            validated_data = dict(
                list(validated_data.items()) +
                list(kwargs.items())
            )

        if self.instance is not None:
            self.instance = self.update(self.instance, validated_data)
            assert self.instance is not None, (
                '`update()` did not return an object instance.'
            )
        else:
            self.instance = self.create(validated_data)
            assert self.instance is not None, (
                '`create()` did not return an object instance.'
            )

        return self.instance

    def is_valid(self, raise_exception=False):
        assert not hasattr(self, 'restore_object'), (
            'Serializer `%s.%s` has old-style version 2 `.restore_object()` '
            'that is no longer compatible with REST framework 3. '
            'Use the new-style `.create()` and `.update()` methods instead.' %
            (self.__class__.__module__, self.__class__.__name__)
        )

        if not hasattr(self, '_validated_data'):
            try:
                self._validated_data = self.run_validation(self._initial_data)
            except ValidationError as exc:
                self._validated_data = {}
                self._errors = exc.detail
            else:
                self._errors = {}

        if self._errors and raise_exception:
            raise ValidationError(self._errors)

        return not bool(self._errors)

    @property
    def data(self):
        if not hasattr(self, '_data'):
            if self.instance is not None and not getattr(self, '_errors', None):
                self._data = self.to_representation(self.instance)
            elif hasattr(self, '_validated_data') and not getattr(self, '_errors', None):
                self._data = self.to_representation(self.validated_data)
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


# Serializer & ListSerializer classes
# -----------------------------------

class ReturnDict(SortedDict):
    """
    Return object from `serialier.data` for the `Serializer` class.
    Includes a backlink to the serializer instance for renderers
    to use if they need richer field information.
    """
    def __init__(self, *args, **kwargs):
        self.serializer = kwargs.pop('serializer')
        super(ReturnDict, self).__init__(*args, **kwargs)


class ReturnList(list):
    """
    Return object from `serialier.data` for the `SerializerList` class.
    Includes a backlink to the serializer instance for renderers
    to use if they need richer field information.
    """
    def __init__(self, *args, **kwargs):
        self.serializer = kwargs.pop('serializer')
        super(ReturnList, self).__init__(*args, **kwargs)


class BoundField(object):
    """
    A field object that also includes `.value` and `.error` properties.
    Returned when iterating over a serializer instance,
    providing an API similar to Django forms and form fields.
    """
    def __init__(self, field, value, errors, prefix=''):
        self._field = field
        self.value = value
        self.errors = errors
        self.name = prefix + self.field_name

    def __getattr__(self, attr_name):
        return getattr(self._field, attr_name)

    @property
    def _proxy_class(self):
        return self._field.__class__

    def __repr__(self):
        return '<%s value=%s errors=%s>' % (
            self.__class__.__name__, self.value, self.errors
        )


class NestedBoundField(BoundField):
    """
    This BoundField additionally implements __iter__ and __getitem__
    in order to support nested bound fields. This class is the type of
    BoundField that is used for serializer fields.
    """
    def __iter__(self):
        for field in self.fields.values():
            yield self[field.field_name]

    def __getitem__(self, key):
        field = self.fields[key]
        value = self.value.get(key) if self.value else None
        error = self.errors.get(key) if self.errors else None
        if isinstance(field, Serializer):
            return NestedBoundField(field, value, error, prefix=self.name + '.')
        return BoundField(field, value, error, prefix=self.name + '.')


class BindingDict(object):
    """
    This dict-like object is used to store fields on a serializer.

    This ensures that whenever fields are added to the serializer we call
    `field.bind()` so that the `field_name` and `parent` attributes
    can be set correctly.
    """
    def __init__(self, serializer):
        self.serializer = serializer
        self.fields = SortedDict()

    def __setitem__(self, key, field):
        self.fields[key] = field
        field.bind(field_name=key, parent=self.serializer)

    def __getitem__(self, key):
        return self.fields[key]

    def __delitem__(self, key):
        del self.fields[key]

    def items(self):
        return self.fields.items()

    def keys(self):
        return self.fields.keys()

    def values(self):
        return self.fields.values()


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
    default_error_messages = {
        'invalid': _('Invalid data. Expected a dictionary, but got {datatype}.')
    }

    @property
    def fields(self):
        if not hasattr(self, '_fields'):
            self._fields = BindingDict(self)
            for key, value in self.get_fields().items():
                self._fields[key] = value
        return self._fields

    def get_fields(self):
        # Every new serializer is created with a clone of the field instances.
        # This allows users to dynamically modify the fields on a serializer
        # instance without affecting every other serializer class.
        return copy.deepcopy(self._declared_fields)

    def get_validators(self):
        return getattr(getattr(self, 'Meta', None), 'validators', [])

    def get_initial(self):
        if self._initial_data is not None:
            return ReturnDict([
                (field_name, field.get_value(self._initial_data))
                for field_name, field in self.fields.items()
                if field.get_value(self._initial_data) is not empty
            ], serializer=self)

        return ReturnDict([
            (field.field_name, field.get_initial())
            for field in self.fields.values()
            if not field.write_only
        ], serializer=self)

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # nested HTML forms.
        if html.is_html_input(dictionary):
            return html.parse_html_dict(dictionary, prefix=self.field_name)
        return dictionary.get(self.field_name, empty)

    def run_validation(self, data=empty):
        """
        We override the default `run_validation`, because the validation
        performed by validators and the `.validate()` method should
        be coerced into an error dictionary with a 'non_fields_error' key.
        """
        if data is empty:
            if getattr(self.root, 'partial', False):
                raise SkipField()
            if self.required:
                self.fail('required')
            return self.get_default()

        if data is None:
            if not self.allow_null:
                self.fail('null')
            return None

        if not isinstance(data, dict):
            message = self.error_messages['invalid'].format(
                datatype=type(data).__name__
            )
            raise ValidationError({
                api_settings.NON_FIELD_ERRORS_KEY: [message]
            })

        value = self.to_internal_value(data)
        try:
            self.run_validators(value)
            value = self.validate(value)
            assert value is not None, '.validate() should return the validated data'
        except ValidationError as exc:
            if isinstance(exc.detail, dict):
                # .validate() errors may be a dict, in which case, use
                # standard {key: list of values} style.
                raise ValidationError(dict([
                    (key, value if isinstance(value, list) else [value])
                    for key, value in exc.detail.items()
                ]))
            elif isinstance(exc.detail, list):
                raise ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: exc.detail
                })
            else:
                raise ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: [exc.detail]
                })

        return value

    def to_internal_value(self, data):
        """
        Dict of native values <- Dict of primitive datatypes.
        """
        ret = {}
        errors = ReturnDict(serializer=self)
        fields = [
            field for field in self.fields.values()
            if (not field.read_only) or (field.default is not empty)
        ]

        for field in fields:
            validate_method = getattr(self, 'validate_' + field.field_name, None)
            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except ValidationError as exc:
                errors[field.field_name] = exc.detail
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise ValidationError(errors)

        return ret

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = ReturnDict(serializer=self)
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            attribute = field.get_attribute(instance)
            if attribute is None:
                value = None
            else:
                value = field.to_representation(attribute)
            transform_method = getattr(self, 'transform_' + field.field_name, None)
            if transform_method is not None:
                value = transform_method(value)

            ret[field.field_name] = value

        return ret

    def validate(self, attrs):
        return attrs

    def __repr__(self):
        return representation.serializer_repr(self, indent=1)

    # The following are used for accessing `BoundField` instances on the
    # serializer, for the purposes of presenting a form-like API onto the
    # field values and field errors.

    def __iter__(self):
        for field in self.fields.values():
            yield self[field.field_name]

    def __getitem__(self, key):
        field = self.fields[key]
        value = self.data.get(key)
        error = self.errors.get(key) if hasattr(self, '_errors') else None
        if isinstance(field, Serializer):
            return NestedBoundField(field, value, error)
        return BoundField(field, value, error)


# There's some replication of `ListField` here,
# but that's probably better than obfuscating the call hierarchy.

class ListSerializer(BaseSerializer):
    child = None
    many = True

    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', copy.deepcopy(self.child))
        assert self.child is not None, '`child` is a required argument.'
        assert not inspect.isclass(self.child), '`child` has not been instantiated.'
        super(ListSerializer, self).__init__(*args, **kwargs)
        self.child.bind(field_name='', parent=self)

    def get_initial(self):
        if self._initial_data is not None:
            return self.to_representation(self._initial_data)
        return ReturnList(serializer=self)

    def get_value(self, dictionary):
        # We override the default field access in order to support
        # lists in HTML forms.
        if html.is_html_input(dictionary):
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
        iterable = data.all() if (hasattr(data, 'all')) else data
        return ReturnList(
            [self.child.to_representation(item) for item in iterable],
            serializer=self
        )

    def create(self, attrs_list):
        return [self.child.create(attrs) for attrs in attrs_list]

    def __repr__(self):
        return representation.list_repr(self, indent=1)


# ModelSerializer & HyperlinkedModelSerializer
# --------------------------------------------

class ModelSerializer(Serializer):
    _field_mapping = ClassLookupDict({
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
        models.NullBooleanField: NullBooleanField,
        models.PositiveIntegerField: IntegerField,
        models.PositiveSmallIntegerField: IntegerField,
        models.SlugField: SlugField,
        models.SmallIntegerField: IntegerField,
        models.TextField: CharField,
        models.TimeField: TimeField,
        models.URLField: URLField,
    })
    _related_class = PrimaryKeyRelatedField

    def create(self, validated_attrs):
        # Check that the user isn't trying to handle a writable nested field.
        # If we don't do this explicitly they'd likely get a confusing
        # error at the point of calling `Model.objects.create()`.
        assert not any(
            isinstance(field, BaseSerializer) and not field.read_only
            for field in self.fields.values()
        ), (
            'The `.create()` method does not suport nested writable fields '
            'by default. Write an explicit `.create()` method for serializer '
            '`%s.%s`, or set `read_only=True` on nested serializer fields.' %
            (self.__class__.__module__, self.__class__.__name__)
        )

        ModelClass = self.Meta.model

        # Remove many-to-many relationships from validated_attrs.
        # They are not valid arguments to the default `.create()` method,
        # as they require that the instance has already been saved.
        info = model_meta.get_field_info(ModelClass)
        many_to_many = {}
        for field_name, relation_info in info.relations.items():
            if relation_info.to_many and (field_name in validated_attrs):
                many_to_many[field_name] = validated_attrs.pop(field_name)

        instance = ModelClass.objects.create(**validated_attrs)

        # Save many-to-many relationships after the instance is created.
        if many_to_many:
            for field_name, value in many_to_many.items():
                setattr(instance, field_name, value)

        return instance

    def update(self, instance, validated_attrs):
        assert not any(
            isinstance(field, BaseSerializer) and not field.read_only
            for field in self.fields.values()
        ), (
            'The `.update()` method does not suport nested writable fields '
            'by default. Write an explicit `.update()` method for serializer '
            '`%s.%s`, or set `read_only=True` on nested serializer fields.' %
            (self.__class__.__module__, self.__class__.__name__)
        )

        for attr, value in validated_attrs.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def get_validators(self):
        field_names = set([
            field.source for field in self.fields.values()
            if (field.source != '*') and ('.' not in field.source)
        ])

        validators = getattr(getattr(self, 'Meta', None), 'validators', [])
        model_class = self.Meta.model

        # Note that we make sure to check `unique_together` both on the
        # base model class, but also on any parent classes.
        for parent_class in [model_class] + list(model_class._meta.parents.keys()):
            for unique_together in parent_class._meta.unique_together:
                if field_names.issuperset(set(unique_together)):
                    validator = UniqueTogetherValidator(
                        queryset=parent_class._default_manager,
                        fields=unique_together
                    )
                    validators.append(validator)

        # Add any unique_for_date/unique_for_month/unique_for_year constraints.
        info = model_meta.get_field_info(model_class)
        for field_name, field in info.fields_and_pk.items():
            if field.unique_for_date and field_name in field_names:
                validator = UniqueForDateValidator(
                    queryset=model_class._default_manager,
                    field=field_name,
                    date_field=field.unique_for_date
                )
                validators.append(validator)

            if field.unique_for_month and field_name in field_names:
                validator = UniqueForMonthValidator(
                    queryset=model_class._default_manager,
                    field=field_name,
                    date_field=field.unique_for_month
                )
                validators.append(validator)

            if field.unique_for_year and field_name in field_names:
                validator = UniqueForYearValidator(
                    queryset=model_class._default_manager,
                    field=field_name,
                    date_field=field.unique_for_year
                )
                validators.append(validator)

        return validators

    def get_fields(self):
        declared_fields = copy.deepcopy(self._declared_fields)

        ret = SortedDict()
        model = getattr(self.Meta, 'model')
        fields = getattr(self.Meta, 'fields', None)
        exclude = getattr(self.Meta, 'exclude', None)
        depth = getattr(self.Meta, 'depth', 0)
        extra_kwargs = getattr(self.Meta, 'extra_kwargs', {})

        assert not (fields and exclude), "Cannot set both 'fields' and 'exclude'."

        extra_kwargs = self._include_additional_options(extra_kwargs)

        # Retrieve metadata about fields & relationships on the model class.
        info = model_meta.get_field_info(model)

        # Use the default set of field names if none is supplied explicitly.
        if fields is None:
            fields = self._get_default_field_names(declared_fields, info)
            exclude = getattr(self.Meta, 'exclude', None)
            if exclude is not None:
                for field_name in exclude:
                    fields.remove(field_name)

        # Determine the set of model fields, and the fields that they map to.
        # We actually only need this to deal with the slightly awkward case
        # of supporting `unique_for_date`/`unique_for_month`/`unique_for_year`.
        model_field_mapping = {}
        for field_name in fields:
            if field_name in declared_fields:
                field = declared_fields[field_name]
                source = field.source or field_name
            else:
                try:
                    source = extra_kwargs[field_name]['source']
                except KeyError:
                    source = field_name
            # Model fields will always have a simple source mapping,
            # they can't be nested attribute lookups.
            if '.' not in source and source != '*':
                model_field_mapping[source] = field_name

        # Determine if we need any additional `HiddenField` or extra keyword
        # arguments to deal with `unique_for` dates that are required to
        # be in the input data in order to validate it.
        unique_fields = {}
        for model_field_name, field_name in model_field_mapping.items():
            try:
                model_field = model._meta.get_field(model_field_name)
            except FieldDoesNotExist:
                continue

            # Deal with each of the `unique_for_*` cases.
            for date_field_name in (
                model_field.unique_for_date,
                model_field.unique_for_month,
                model_field.unique_for_year
            ):
                if date_field_name is None:
                    continue

                # Get the model field that is refered too.
                date_field = model._meta.get_field(date_field_name)

                if date_field.auto_now_add:
                    default = CreateOnlyDefault(timezone.now)
                elif date_field.auto_now:
                    default = timezone.now
                elif date_field.has_default():
                    default = model_field.default
                else:
                    default = empty

                if date_field_name in model_field_mapping:
                    # The corresponding date field is present in the serializer
                    if date_field_name not in extra_kwargs:
                        extra_kwargs[date_field_name] = {}
                    if default is empty:
                        if 'required' not in extra_kwargs[date_field_name]:
                            extra_kwargs[date_field_name]['required'] = True
                    else:
                        if 'default' not in extra_kwargs[date_field_name]:
                            extra_kwargs[date_field_name]['default'] = default
                else:
                    # The corresponding date field is not present in the,
                    # serializer. We have a default to use for the date, so
                    # add in a hidden field that populates it.
                    unique_fields[date_field_name] = HiddenField(default=default)

        # Now determine the fields that should be included on the serializer.
        for field_name in fields:
            if field_name in declared_fields:
                # Field is explicitly declared on the class, use that.
                ret[field_name] = declared_fields[field_name]
                continue

            elif field_name in info.fields_and_pk:
                # Create regular model fields.
                model_field = info.fields_and_pk[field_name]
                field_cls = self._field_mapping[model_field]
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
                if not issubclass(field_cls, CharField):
                    # `allow_blank` is only valid for textual fields.
                    kwargs.pop('allow_blank', None)

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

            elif field_name == api_settings.URL_FIELD_NAME:
                # Create the URL field.
                field_cls = HyperlinkedIdentityField
                kwargs = get_url_kwargs(model)

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
            extras = extra_kwargs.get(field_name, {})
            if extras.get('read_only', False):
                for attr in [
                    'required', 'default', 'allow_blank', 'allow_null',
                    'min_length', 'max_length', 'min_value', 'max_value',
                    'validators', 'queryset'
                ]:
                    kwargs.pop(attr, None)
            kwargs.update(extras)

            # Create the serializer field.
            ret[field_name] = field_cls(**kwargs)

        for field_name, field in unique_fields.items():
            ret[field_name] = field

        return ret

    def _include_additional_options(self, extra_kwargs):
        read_only_fields = getattr(self.Meta, 'read_only_fields', None)
        if read_only_fields is not None:
            for field_name in read_only_fields:
                kwargs = extra_kwargs.get(field_name, {})
                kwargs['read_only'] = True
                extra_kwargs[field_name] = kwargs

        # These are all pending deprecation.
        write_only_fields = getattr(self.Meta, 'write_only_fields', None)
        if write_only_fields is not None:
            warnings.warn(
                "The `Meta.write_only_fields` option is pending deprecation. "
                "Use `Meta.extra_kwargs={<field_name>: {'write_only': True}}` instead.",
                PendingDeprecationWarning,
                stacklevel=3
            )
            for field_name in write_only_fields:
                kwargs = extra_kwargs.get(field_name, {})
                kwargs['write_only'] = True
                extra_kwargs[field_name] = kwargs

        view_name = getattr(self.Meta, 'view_name', None)
        if view_name is not None:
            warnings.warn(
                "The `Meta.view_name` option is pending deprecation. "
                "Use `Meta.extra_kwargs={'url': {'view_name': ...}}` instead.",
                PendingDeprecationWarning,
                stacklevel=3
            )
            kwargs = extra_kwargs.get(api_settings.URL_FIELD_NAME, {})
            kwargs['view_name'] = view_name
            extra_kwargs[api_settings.URL_FIELD_NAME] = kwargs

        lookup_field = getattr(self.Meta, 'lookup_field', None)
        if lookup_field is not None:
            warnings.warn(
                "The `Meta.lookup_field` option is pending deprecation. "
                "Use `Meta.extra_kwargs={'url': {'lookup_field': ...}}` instead.",
                PendingDeprecationWarning,
                stacklevel=3
            )
            kwargs = extra_kwargs.get(api_settings.URL_FIELD_NAME, {})
            kwargs['lookup_field'] = lookup_field
            extra_kwargs[api_settings.URL_FIELD_NAME] = kwargs

        return extra_kwargs

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
