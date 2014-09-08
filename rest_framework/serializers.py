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
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import six
from collections import namedtuple, OrderedDict
from rest_framework.fields import empty, set_value, Field, SkipField
from rest_framework.settings import api_settings
from rest_framework.utils import html
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
                self._data = {
                    field_name: field.get_value(self._initial_data)
                    for field_name, field in self.fields.items()
                }
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

    Any fields included as attributes on either the class or it's superclasses
    will be include in the `base_fields` dictionary.
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

        return OrderedDict(fields)

    def __new__(cls, name, bases, attrs):
        attrs['base_fields'] = cls._get_fields(bases, attrs)
        return super(SerializerMetaclass, cls).__new__(cls, name, bases, attrs)


@six.add_metaclass(SerializerMetaclass)
class Serializer(BaseSerializer):

    def __new__(cls, *args, **kwargs):
        many = kwargs.pop('many', False)
        if many:
            class DynamicListSerializer(ListSerializer):
                child = cls()
            return DynamicListSerializer(*args, **kwargs)
        return super(Serializer, cls).__new__(cls)

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
        return {
            field.field_name: field.get_initial()
            for field in self.fields.values()
        }

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
                validated_value = field.validate(primitive_value)
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
        except ValidationError, exc:
            raise ValidationError({'non_field_errors': exc.messages})

    def to_primative(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
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


def _resolve_model(obj):
    """
    Resolve supplied `obj` to a Django model class.

    `obj` must be a Django model class itself, or a string
    representation of one.  Useful in situtations like GH #1225 where
    Django may not have resolved a string-based reference to a model in
    another model's foreign key definition.

    String representations should have the format:
        'appname.ModelName'
    """
    if isinstance(obj, six.string_types) and len(obj.split('.')) == 2:
        app_name, model_name = obj.split('.')
        return models.get_model(app_name, model_name)
    elif inspect.isclass(obj) and issubclass(obj, models.Model):
        return obj
    else:
        raise ValueError("{0} is not a Django model".format(obj))


class ModelSerializerOptions(object):
    """
    Meta class options for ModelSerializer
    """
    def __init__(self, meta):
        self.model = getattr(meta, 'model')
        self.fields = getattr(meta, 'fields', ())
        self.depth = getattr(meta, 'depth', 0)


class ModelSerializer(Serializer):
    field_mapping = {
        models.AutoField: IntegerField,
        # models.FloatField: FloatField,
        models.IntegerField: IntegerField,
        models.PositiveIntegerField: IntegerField,
        models.SmallIntegerField: IntegerField,
        models.PositiveSmallIntegerField: IntegerField,
        models.DateTimeField: DateTimeField,
        models.DateField: DateField,
        models.TimeField: TimeField,
        # models.DecimalField: DecimalField,
        models.EmailField: EmailField,
        models.CharField: CharField,
        models.URLField: URLField,
        # models.SlugField: SlugField,
        models.TextField: CharField,
        models.CommaSeparatedIntegerField: CharField,
        models.BooleanField: BooleanField,
        models.NullBooleanField: BooleanField,
        models.FileField: FileField,
        # models.ImageField: ImageField,
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
            fields = OrderedDict([
                (key, fields[key]) for key in self.opts.fields
            ])

        return fields

    def get_default_fields(self):
        """
        Return all the fields that should be serialized for the model.
        """
        cls = self.opts.model
        opts = cls._meta.concrete_model._meta
        ret = OrderedDict()
        nested = bool(self.opts.depth)

        # Deal with adding the primary key field
        pk_field = opts.pk
        while pk_field.rel and pk_field.rel.parent_link:
            # If model is a child via multitable inheritance, use parent's pk
            pk_field = pk_field.rel.to._meta.pk

        serializer_pk_field = self.get_pk_field(pk_field)
        if serializer_pk_field:
            ret[pk_field.name] = serializer_pk_field

        # Deal with forward relationships
        forward_rels = [field for field in opts.fields if field.serialize]
        forward_rels += [field for field in opts.many_to_many if field.serialize]

        for model_field in forward_rels:
            has_through_model = False

            if model_field.rel:
                to_many = isinstance(model_field,
                                     models.fields.related.ManyToManyField)
                related_model = _resolve_model(model_field.rel.to)

                if to_many and not model_field.rel.through._meta.auto_created:
                    has_through_model = True

            if model_field.rel and nested:
                field = self.get_nested_field(model_field, related_model, to_many)
            elif model_field.rel:
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

            if (
                is_m2m and
                hasattr(relation.field.rel, 'through') and
                not relation.field.rel.through._meta.auto_created
            ):
                has_through_model = True

            if nested:
                field = self.get_nested_field(None, related_model, to_many)
            else:
                field = self.get_related_field(None, related_model, to_many)

            if field:
                if has_through_model:
                    field.read_only = True

                ret[accessor_name] = field

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

        kwargs = {}
        #     'queryset': related_model._default_manager,
        #     'many': to_many
        # }

        if model_field:
            kwargs['required'] = not(model_field.null or model_field.blank)
            #  if model_field.help_text is not None:
            #      kwargs['help_text'] = model_field.help_text
            if model_field.verbose_name is not None:
                kwargs['label'] = model_field.verbose_name
            if not model_field.editable:
                kwargs['read_only'] = True
            if model_field.verbose_name is not None:
                kwargs['label'] = model_field.verbose_name

        return IntegerField(**kwargs)
        # TODO: return PrimaryKeyRelatedField(**kwargs)

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

        if model_field.validators is not None:
            kwargs['validators'] = model_field.validators

        # if model_field.help_text is not None:
        #     kwargs['help_text'] = model_field.help_text

        # TODO: TypedChoiceField?
        if model_field.flatchoices:  # This ModelField contains choices
            kwargs['choices'] = model_field.flatchoices
            if model_field.null:
                kwargs['empty'] = None
            return ChoiceField(**kwargs)

        # put this below the ChoiceField because min_value isn't a valid initializer
        if issubclass(model_field.__class__, models.PositiveIntegerField) or \
                issubclass(model_field.__class__, models.PositiveSmallIntegerField):
            kwargs['min_value'] = 0

        if model_field.null and \
                issubclass(model_field.__class__, (models.CharField, models.TextField)):
            kwargs['allow_none'] = True

        # attribute_dict = {
        #     models.CharField: ['max_length'],
        #     models.CommaSeparatedIntegerField: ['max_length'],
        #     models.DecimalField: ['max_digits', 'decimal_places'],
        #     models.EmailField: ['max_length'],
        #     models.FileField: ['max_length'],
        #     models.ImageField: ['max_length'],
        #     models.SlugField: ['max_length'],
        #     models.URLField: ['max_length'],
        # }

        # if model_field.__class__ in attribute_dict:
        #     attributes = attribute_dict[model_field.__class__]
        #     for attribute in attributes:
        #         kwargs.update({attribute: getattr(model_field, attribute)})

        try:
            return self.field_mapping[model_field.__class__](**kwargs)
        except KeyError:
            return ModelField(model_field=model_field, **kwargs)


class HyperlinkedModelSerializerOptions(ModelSerializerOptions):
    """
    Options for HyperlinkedModelSerializer
    """
    def __init__(self, meta):
        super(HyperlinkedModelSerializerOptions, self).__init__(meta)
        self.view_name = getattr(meta, 'view_name', None)
        self.lookup_field = getattr(meta, 'lookup_field', None)
        self.url_field_name = getattr(meta, 'url_field_name', api_settings.URL_FIELD_NAME)


class HyperlinkedModelSerializer(ModelSerializer):
    _options_class = HyperlinkedModelSerializerOptions
    _default_view_name = '%(model_name)s-detail'
    _hyperlink_field_class = HyperlinkedRelatedField
    _hyperlink_identify_field_class = HyperlinkedIdentityField

    def get_default_fields(self):
        fields = super(HyperlinkedModelSerializer, self).get_default_fields()

        if self.opts.view_name is None:
            self.opts.view_name = self._get_default_view_name(self.opts.model)

        if self.opts.url_field_name not in fields:
            url_field = self._hyperlink_identify_field_class(
                view_name=self.opts.view_name,
                lookup_field=self.opts.lookup_field
            )
            ret = fields.__class__()
            ret[self.opts.url_field_name] = url_field
            ret.update(fields)
            fields = ret

        return fields

    def get_pk_field(self, model_field):
        if self.opts.fields and model_field.name in self.opts.fields:
            return self.get_field(model_field)

    def get_related_field(self, model_field, related_model, to_many):
        """
        Creates a default instance of a flat relational field.
        """
        # TODO: filter queryset using:
        # .using(db).complex_filter(self.rel.limit_choices_to)
        # kwargs = {
        #     'queryset': related_model._default_manager,
        #     'view_name': self._get_default_view_name(related_model),
        #     'many': to_many
        # }
        kwargs = {}

        if model_field:
            kwargs['required'] = not(model_field.null or model_field.blank)
            # if model_field.help_text is not None:
            #     kwargs['help_text'] = model_field.help_text
            if model_field.verbose_name is not None:
                kwargs['label'] = model_field.verbose_name

        return IntegerField(**kwargs)
        # if self.opts.lookup_field:
        #     kwargs['lookup_field'] = self.opts.lookup_field

        # return self._hyperlink_field_class(**kwargs)

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
