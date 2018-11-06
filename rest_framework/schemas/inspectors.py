# -*- coding: utf-8 -*-
"""
inspectors.py   # Per-endpoint view introspection

See schemas.__init__.py for package overview.
"""
import re
import warnings
from collections import OrderedDict
from weakref import WeakKeyDictionary

from django.db import models
from django.utils.encoding import force_text, smart_text
from django.utils.six.moves.urllib import parse as urlparse
from django.utils.translation import ugettext_lazy as _

from rest_framework import exceptions, serializers
from rest_framework.compat import coreapi, coreschema, uritemplate
from rest_framework.settings import api_settings
from rest_framework.utils import formatting

from .utils import is_list_view

header_regex = re.compile('^[a-zA-Z][0-9A-Za-z_]*:')


def field_to_schema(field):
    title = force_text(field.label) if field.label else ''
    description = force_text(field.help_text) if field.help_text else ''

    if isinstance(field, (serializers.ListSerializer, serializers.ListField)):
        child_schema = field_to_schema(field.child)
        return coreschema.Array(
            items=child_schema,
            title=title,
            description=description
        )
    elif isinstance(field, serializers.DictField):
        return coreschema.Object(
            title=title,
            description=description
        )
    elif isinstance(field, serializers.Serializer):
        return coreschema.Object(
            properties=OrderedDict([
                (key, field_to_schema(value))
                for key, value
                in field.fields.items()
            ]),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.ManyRelatedField):
        return coreschema.Array(
            items=coreschema.String(),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.PrimaryKeyRelatedField):
        schema_cls = coreschema.String
        model = getattr(field.queryset, 'model', None)
        if model is not None:
            model_field = model._meta.pk
            if isinstance(model_field, models.AutoField):
                schema_cls = coreschema.Integer
        return schema_cls(title=title, description=description)
    elif isinstance(field, serializers.RelatedField):
        return coreschema.String(title=title, description=description)
    elif isinstance(field, serializers.MultipleChoiceField):
        return coreschema.Array(
            items=coreschema.Enum(enum=list(field.choices)),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.ChoiceField):
        return coreschema.Enum(
            enum=list(field.choices),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.BooleanField):
        return coreschema.Boolean(title=title, description=description)
    elif isinstance(field, (serializers.DecimalField, serializers.FloatField)):
        return coreschema.Number(title=title, description=description)
    elif isinstance(field, serializers.IntegerField):
        return coreschema.Integer(title=title, description=description)
    elif isinstance(field, serializers.DateField):
        return coreschema.String(
            title=title,
            description=description,
            format='date'
        )
    elif isinstance(field, serializers.DateTimeField):
        return coreschema.String(
            title=title,
            description=description,
            format='date-time'
        )
    elif isinstance(field, serializers.JSONField):
        return coreschema.Object(title=title, description=description)

    if field.style.get('base_template') == 'textarea.html':
        return coreschema.String(
            title=title,
            description=description,
            format='textarea'
        )

    return coreschema.String(title=title, description=description)


def get_pk_description(model, model_field):
    if isinstance(model_field, models.AutoField):
        value_type = _('unique integer value')
    elif isinstance(model_field, models.UUIDField):
        value_type = _('UUID string')
    else:
        value_type = _('unique value')

    return _('A {value_type} identifying this {name}.').format(
        value_type=value_type,
        name=model._meta.verbose_name,
    )


class ViewInspector(object):
    """
    Descriptor class on APIView.

    Provide subclass for per-view schema generation
    """

    def __init__(self):
        self.instance_schemas = WeakKeyDictionary()

    def __get__(self, instance, owner):
        """
        Enables `ViewInspector` as a Python _Descriptor_.

        This is how `view.schema` knows about `view`.

        `__get__` is called when the descriptor is accessed on the owner.
        (That will be when view.schema is called in our case.)

        `owner` is always the owner class. (An APIView, or subclass for us.)
        `instance` is the view instance or `None` if accessed from the class,
        rather than an instance.

        See: https://docs.python.org/3/howto/descriptor.html for info on
        descriptor usage.
        """
        if instance in self.instance_schemas:
            return self.instance_schemas[instance]

        self.view = instance
        return self

    def __set__(self, instance, other):
        self.instance_schemas[instance] = other
        if other is not None:
            other.view = instance

    @property
    def view(self):
        """View property."""
        assert self._view is not None, "Schema generation REQUIRES a view instance. (Hint: you accessed `schema` from the view class rather than an instance.)"
        return self._view

    @view.setter
    def view(self, value):
        self._view = value

    @view.deleter
    def view(self):
        self._view = None

    def get_link(self, path, method, base_url):
        """
        Generate `coreapi.Link` for self.view, path and method.

        This is the main _public_ access point.

        Parameters:

        * path: Route path for view from URLConf.
        * method: The HTTP request method.
        * base_url: The project "mount point" as given to SchemaGenerator
        """
        raise NotImplementedError(".get_link() must be overridden.")


class AutoSchema(ViewInspector):
    """
    Default inspector for APIView

    Responsible for per-view instrospection and schema generation.
    """
    def __init__(self, manual_fields=None):
        """
        Parameters:

        * `manual_fields`: list of `coreapi.Field` instances that
            will be added to auto-generated fields, overwriting on `Field.name`
        """
        super(AutoSchema, self).__init__()
        if manual_fields is None:
            manual_fields = []
        self._manual_fields = manual_fields

    def get_link(self, path, method, base_url):
        fields = self.get_path_fields(path, method)
        fields += self.get_serializer_fields(path, method)
        fields += self.get_pagination_fields(path, method)
        fields += self.get_filter_fields(path, method)

        manual_fields = self.get_manual_fields(path, method)
        fields = self.update_fields(fields, manual_fields)

        if fields and any([field.location in ('form', 'body') for field in fields]):
            encoding = self.get_encoding(path, method)
        else:
            encoding = None

        description = self.get_description(path, method)

        if base_url and path.startswith('/'):
            path = path[1:]

        return coreapi.Link(
            url=urlparse.urljoin(base_url, path),
            action=method.lower(),
            encoding=encoding,
            fields=fields,
            description=description
        )

    def get_description(self, path, method):
        """
        Determine a link description.

        This will be based on the method docstring if one exists,
        or else the class docstring.
        """
        view = self.view

        method_name = getattr(view, 'action', method.lower())
        method_docstring = getattr(view, method_name, None).__doc__
        if method_docstring:
            # An explicit docstring on the method or action.
            return self._get_description_section(view, method.lower(), formatting.dedent(smart_text(method_docstring)))
        else:
            return self._get_description_section(view, getattr(view, 'action', method.lower()), view.get_view_description())

    def _get_description_section(self, view, header, description):
        lines = [line for line in description.splitlines()]
        current_section = ''
        sections = {'': ''}

        for line in lines:
            if header_regex.match(line):
                current_section, seperator, lead = line.partition(':')
                sections[current_section] = lead.strip()
            else:
                sections[current_section] += '\n' + line

        # TODO: SCHEMA_COERCE_METHOD_NAMES appears here and in `SchemaGenerator.get_keys`
        coerce_method_names = api_settings.SCHEMA_COERCE_METHOD_NAMES
        if header in sections:
            return sections[header].strip()
        if header in coerce_method_names:
            if coerce_method_names[header] in sections:
                return sections[coerce_method_names[header]].strip()
        return sections[''].strip()

    def get_path_fields(self, path, method):
        """
        Return a list of `coreapi.Field` instances corresponding to any
        templated path variables.
        """
        view = self.view
        model = getattr(getattr(view, 'queryset', None), 'model', None)
        fields = []

        for variable in uritemplate.variables(path):
            title = ''
            description = ''
            schema_cls = coreschema.String
            kwargs = {}
            if model is not None:
                # Attempt to infer a field description if possible.
                try:
                    model_field = model._meta.get_field(variable)
                except Exception:
                    model_field = None

                if model_field is not None and model_field.verbose_name:
                    title = force_text(model_field.verbose_name)

                if model_field is not None and model_field.help_text:
                    description = force_text(model_field.help_text)
                elif model_field is not None and model_field.primary_key:
                    description = get_pk_description(model, model_field)

                if hasattr(view, 'lookup_value_regex') and view.lookup_field == variable:
                    kwargs['pattern'] = view.lookup_value_regex
                elif isinstance(model_field, models.AutoField):
                    schema_cls = coreschema.Integer

            field = coreapi.Field(
                name=variable,
                location='path',
                required=True,
                schema=schema_cls(title=title, description=description, **kwargs)
            )
            fields.append(field)

        return fields

    def get_serializer_fields(self, path, method):
        """
        Return a list of `coreapi.Field` instances corresponding to any
        request body input, as determined by the serializer class.
        """
        view = self.view

        if method not in ('PUT', 'PATCH', 'POST'):
            return []

        if not hasattr(view, 'get_serializer'):
            return []

        try:
            serializer = view.get_serializer()
        except exceptions.APIException:
            serializer = None
            warnings.warn('{}.get_serializer() raised an exception during '
                          'schema generation. Serializer fields will not be '
                          'generated for {} {}.'
                          .format(view.__class__.__name__, method, path))

        if isinstance(serializer, serializers.ListSerializer):
            return [
                coreapi.Field(
                    name='data',
                    location='body',
                    required=True,
                    schema=coreschema.Array()
                )
            ]

        if not isinstance(serializer, serializers.Serializer):
            return []

        fields = []
        for field in serializer.fields.values():
            if field.read_only or isinstance(field, serializers.HiddenField):
                continue

            required = field.required and method != 'PATCH'
            field = coreapi.Field(
                name=field.field_name,
                location='form',
                required=required,
                schema=field_to_schema(field)
            )
            fields.append(field)

        return fields

    def get_pagination_fields(self, path, method):
        view = self.view

        if not is_list_view(path, method, view):
            return []

        pagination = getattr(view, 'pagination_class', None)
        if not pagination:
            return []

        paginator = view.pagination_class()
        return paginator.get_schema_fields(view)

    def _allows_filters(self, path, method):
        """
        Determine whether to include filter Fields in schema.

        Default implementation looks for ModelViewSet or GenericAPIView
        actions/methods that cause filtering on the default implementation.

        Override to adjust behaviour for your view.

        Note: Introduced in v3.7: Initially "private" (i.e. with leading underscore)
            to allow changes based on user experience.
        """
        if getattr(self.view, 'filter_backends', None) is None:
            return False

        if hasattr(self.view, 'action'):
            return self.view.action in ["list", "retrieve", "update", "partial_update", "destroy"]

        return method.lower() in ["get", "put", "patch", "delete"]

    def get_filter_fields(self, path, method):
        if not self._allows_filters(path, method):
            return []

        fields = []
        for filter_backend in self.view.filter_backends:
            fields += filter_backend().get_schema_fields(self.view)
        return fields

    def get_manual_fields(self, path, method):
        return self._manual_fields

    @staticmethod
    def update_fields(fields, update_with):
        """
        Update list of coreapi.Field instances, overwriting on `Field.name`.

        Utility function to handle replacing coreapi.Field fields
        from a list by name. Used to handle `manual_fields`.

        Parameters:

        * `fields`: list of `coreapi.Field` instances to update
        * `update_with: list of `coreapi.Field` instances to add or replace.
        """
        if not update_with:
            return fields

        by_name = OrderedDict((f.name, f) for f in fields)
        for f in update_with:
            by_name[f.name] = f
        fields = list(by_name.values())
        return fields

    def get_encoding(self, path, method):
        """
        Return the 'encoding' parameter to use for a given endpoint.
        """
        view = self.view

        # Core API supports the following request encodings over HTTP...
        supported_media_types = {
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
        }
        parser_classes = getattr(view, 'parser_classes', [])
        for parser_class in parser_classes:
            media_type = getattr(parser_class, 'media_type', None)
            if media_type in supported_media_types:
                return media_type
            # Raw binary uploads are supported with "application/octet-stream"
            if media_type == '*/*':
                return 'application/octet-stream'

        return None


class ManualSchema(ViewInspector):
    """
    Allows providing a list of coreapi.Fields,
    plus an optional description.
    """
    def __init__(self, fields, description='', encoding=None):
        """
        Parameters:

        * `fields`: list of `coreapi.Field` instances.
        * `descripton`: String description for view. Optional.
        """
        super(ManualSchema, self).__init__()
        assert all(isinstance(f, coreapi.Field) for f in fields), "`fields` must be a list of coreapi.Field instances"
        self._fields = fields
        self._description = description
        self._encoding = encoding

    def get_link(self, path, method, base_url):

        if base_url and path.startswith('/'):
            path = path[1:]

        return coreapi.Link(
            url=urlparse.urljoin(base_url, path),
            action=method.lower(),
            encoding=self._encoding,
            fields=self._fields,
            description=self._description
        )


class DefaultSchema(ViewInspector):
    """Allows overriding AutoSchema using DEFAULT_SCHEMA_CLASS setting"""
    def __get__(self, instance, owner):
        result = super(DefaultSchema, self).__get__(instance, owner)
        if not isinstance(result, DefaultSchema):
            return result

        inspector_class = api_settings.DEFAULT_SCHEMA_CLASS
        assert issubclass(inspector_class, ViewInspector), "DEFAULT_SCHEMA_CLASS must be set to a ViewInspector (usually an AutoSchema) subclass"
        inspector = inspector_class()
        inspector.view = instance
        return inspector
