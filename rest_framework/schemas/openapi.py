import warnings
from operator import attrgetter
from urllib.parse import urljoin

from django.core.validators import (
    DecimalValidator, EmailValidator, MaxLengthValidator, MaxValueValidator,
    MinLengthValidator, MinValueValidator, RegexValidator, URLValidator
)
from django.db import models
from django.utils.encoding import force_str

from rest_framework import exceptions, renderers, serializers
from rest_framework.compat import uritemplate
from rest_framework.fields import _UnvalidatedField, empty

from .generators import BaseSchemaGenerator
from .inspectors import ViewInspector
from .utils import get_pk_description, is_list_view


class SchemaGenerator(BaseSchemaGenerator):

    def get_info(self):
        # Title and version are required by openapi specification 3.x
        info = {
            'title': self.title or '',
            'version': self.version or ''
        }

        if self.description is not None:
            info['description'] = self.description

        return info

    def get_paths(self, request=None):
        result = {}

        paths, view_endpoints = self._get_paths_and_endpoints(request)

        # Only generate the path prefix for paths that will be included
        if not paths:
            return None

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            operation = view.schema.get_operation(path, method)
            # Normalise path for any provided mount url.
            if path.startswith('/'):
                path = path[1:]
            path = urljoin(self.url or '/', path)

            result.setdefault(path, {})
            result[path][method.lower()] = operation

        return result

    def get_schema(self, request=None, public=False):
        """
        Generate a OpenAPI schema.
        """
        self._initialise_endpoints()

        paths = self.get_paths(None if public else request)
        if not paths:
            return None

        schema = {
            'openapi': '3.0.2',
            'info': self.get_info(),
            'paths': paths,
        }

        return schema

# View Inspectors


class AutoSchema(ViewInspector):

    request_media_types = []
    response_media_types = []

    method_mapping = {
        'get': 'Retrieve',
        'post': 'Create',
        'put': 'Update',
        'patch': 'PartialUpdate',
        'delete': 'Destroy',
    }

    def get_operation(self, path, method):
        operation = {}

        operation['operationId'] = self._get_operation_id(path, method)
        operation['description'] = self.get_description(path, method)

        parameters = []
        parameters += self._get_path_parameters(path, method)
        parameters += self._get_pagination_parameters(path, method)
        parameters += self._get_filter_parameters(path, method)
        operation['parameters'] = parameters

        request_body = self._get_request_body(path, method)
        if request_body:
            operation['requestBody'] = request_body
        operation['responses'] = self._get_responses(path, method)

        return operation

    def _get_operation_id(self, path, method):
        """
        Compute an operation ID from the model, serializer or view name.
        """
        method_name = getattr(self.view, 'action', method.lower())
        if is_list_view(path, method, self.view):
            action = 'list'
        elif method_name not in self.method_mapping:
            action = method_name
        else:
            action = self.method_mapping[method.lower()]

        # Try to deduce the ID from the view's model
        model = getattr(getattr(self.view, 'queryset', None), 'model', None)
        if model is not None:
            name = model.__name__

        # Try with the serializer class name
        elif hasattr(self.view, 'get_serializer_class'):
            name = self.view.get_serializer_class().__name__
            if name.endswith('Serializer'):
                name = name[:-10]

        # Fallback to the view name
        else:
            name = self.view.__class__.__name__
            if name.endswith('APIView'):
                name = name[:-7]
            elif name.endswith('View'):
                name = name[:-4]

            # Due to camel-casing of classes and `action` being lowercase, apply title in order to find if action truly
            # comes at the end of the name
            if name.endswith(action.title()):  # ListView, UpdateAPIView, ThingDelete ...
                name = name[:-len(action)]

        if action == 'list' and not name.endswith('s'):  # listThings instead of listThing
            name += 's'

        return action + name

    def _get_path_parameters(self, path, method):
        """
        Return a list of parameters from templated path variables.
        """
        assert uritemplate, '`uritemplate` must be installed for OpenAPI schema support.'

        model = getattr(getattr(self.view, 'queryset', None), 'model', None)
        parameters = []

        for variable in uritemplate.variables(path):
            description = ''
            if model is not None:  # TODO: test this.
                # Attempt to infer a field description if possible.
                try:
                    model_field = model._meta.get_field(variable)
                except Exception:
                    model_field = None

                if model_field is not None and model_field.help_text:
                    description = force_str(model_field.help_text)
                elif model_field is not None and model_field.primary_key:
                    description = get_pk_description(model, model_field)

            parameter = {
                "name": variable,
                "in": "path",
                "required": True,
                "description": description,
                'schema': {
                    'type': 'string',  # TODO: integer, pattern, ...
                },
            }
            parameters.append(parameter)

        return parameters

    def _get_filter_parameters(self, path, method):
        if not self._allows_filters(path, method):
            return []
        parameters = []
        for filter_backend in self.view.filter_backends:
            parameters += filter_backend().get_schema_operation_parameters(self.view)
        return parameters

    def _allows_filters(self, path, method):
        """
        Determine whether to include filter Fields in schema.

        Default implementation looks for ModelViewSet or GenericAPIView
        actions/methods that cause filtering on the default implementation.
        """
        if getattr(self.view, 'filter_backends', None) is None:
            return False
        if hasattr(self.view, 'action'):
            return self.view.action in ["list", "retrieve", "update", "partial_update", "destroy"]
        return method.lower() in ["get", "put", "patch", "delete"]

    def _get_pagination_parameters(self, path, method):
        view = self.view

        if not is_list_view(path, method, view):
            return []

        paginator = self._get_paginator()
        if not paginator:
            return []

        return paginator.get_schema_operation_parameters(view)

    def _map_field(self, field):

        # Nested Serializers, `many` or not.
        if isinstance(field, serializers.ListSerializer):
            return {
                'type': 'array',
                'items': self._map_serializer(field.child)
            }
        if isinstance(field, serializers.Serializer):
            data = self._map_serializer(field)
            data['type'] = 'object'
            return data

        # Related fields.
        if isinstance(field, serializers.ManyRelatedField):
            return {
                'type': 'array',
                'items': self._map_field(field.child_relation)
            }
        if isinstance(field, serializers.PrimaryKeyRelatedField):
            model = getattr(field.queryset, 'model', None)
            if model is not None:
                model_field = model._meta.pk
                if isinstance(model_field, models.AutoField):
                    return {'type': 'integer'}

        # ChoiceFields (single and multiple).
        # Q:
        # - Is 'type' required?
        # - can we determine the TYPE of a choicefield?
        if isinstance(field, serializers.MultipleChoiceField):
            return {
                'type': 'array',
                'items': {
                    'enum': list(field.choices)
                },
            }

        if isinstance(field, serializers.ChoiceField):
            return {
                'enum': list(field.choices),
            }

        # ListField.
        if isinstance(field, serializers.ListField):
            mapping = {
                'type': 'array',
                'items': {},
            }
            if not isinstance(field.child, _UnvalidatedField):
                map_field = self._map_field(field.child)
                items = {
                    "type": map_field.get('type')
                }
                if 'format' in map_field:
                    items['format'] = map_field.get('format')
                mapping['items'] = items
            return mapping

        # DateField and DateTimeField type is string
        if isinstance(field, serializers.DateField):
            return {
                'type': 'string',
                'format': 'date',
            }

        if isinstance(field, serializers.DateTimeField):
            return {
                'type': 'string',
                'format': 'date-time',
            }

        # "Formats such as "email", "uuid", and so on, MAY be used even though undefined by this specification."
        # see: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types
        # see also: https://swagger.io/docs/specification/data-models/data-types/#string
        if isinstance(field, serializers.EmailField):
            return {
                'type': 'string',
                'format': 'email'
            }

        if isinstance(field, serializers.URLField):
            return {
                'type': 'string',
                'format': 'uri'
            }

        if isinstance(field, serializers.UUIDField):
            return {
                'type': 'string',
                'format': 'uuid'
            }

        if isinstance(field, serializers.IPAddressField):
            content = {
                'type': 'string',
            }
            if field.protocol != 'both':
                content['format'] = field.protocol
            return content

        # DecimalField has multipleOf based on decimal_places
        if isinstance(field, serializers.DecimalField):
            content = {
                'type': 'number'
            }
            if field.decimal_places:
                content['multipleOf'] = float('.' + (field.decimal_places - 1) * '0' + '1')
            if field.max_whole_digits:
                content['maximum'] = int(field.max_whole_digits * '9') + 1
                content['minimum'] = -content['maximum']
            self._map_min_max(field, content)
            return content

        if isinstance(field, serializers.FloatField):
            content = {
                'type': 'number'
            }
            self._map_min_max(field, content)
            return content

        if isinstance(field, serializers.IntegerField):
            content = {
                'type': 'integer'
            }
            self._map_min_max(field, content)
            # 2147483647 is max for int32_size, so we use int64 for format
            if int(content.get('maximum', 0)) > 2147483647 or int(content.get('minimum', 0)) > 2147483647:
                content['format'] = 'int64'
            return content

        if isinstance(field, serializers.FileField):
            return {
                'type': 'string',
                'format': 'binary'
            }

        # Simplest cases, default to 'string' type:
        FIELD_CLASS_SCHEMA_TYPE = {
            serializers.BooleanField: 'boolean',
            serializers.JSONField: 'object',
            serializers.DictField: 'object',
            serializers.HStoreField: 'object',
        }
        return {'type': FIELD_CLASS_SCHEMA_TYPE.get(field.__class__, 'string')}

    def _map_min_max(self, field, content):
        if field.max_value:
            content['maximum'] = field.max_value
        if field.min_value:
            content['minimum'] = field.min_value

    def _map_serializer(self, serializer):
        # Assuming we have a valid serializer instance.
        # TODO:
        #   - field is Nested or List serializer.
        #   - Handle read_only/write_only for request/response differences.
        #       - could do this with readOnly/writeOnly and then filter dict.
        required = []
        properties = {}

        for field in serializer.fields.values():
            if isinstance(field, serializers.HiddenField):
                continue

            if field.required:
                required.append(field.field_name)

            schema = self._map_field(field)
            if field.read_only:
                schema['readOnly'] = True
            if field.write_only:
                schema['writeOnly'] = True
            if field.allow_null:
                schema['nullable'] = True
            if field.default and field.default != empty:  # why don't they use None?!
                schema['default'] = field.default
            if field.help_text:
                schema['description'] = str(field.help_text)
            self._map_field_validators(field, schema)

            properties[field.field_name] = schema

        result = {
            'properties': properties
        }
        if required:
            result['required'] = required

        return result

    def _map_field_validators(self, field, schema):
        """
        map field validators
        """
        for v in field.validators:
            # "Formats such as "email", "uuid", and so on, MAY be used even though undefined by this specification."
            # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#data-types
            if isinstance(v, EmailValidator):
                schema['format'] = 'email'
            if isinstance(v, URLValidator):
                schema['format'] = 'uri'
            if isinstance(v, RegexValidator):
                schema['pattern'] = v.regex.pattern
            elif isinstance(v, MaxLengthValidator):
                attr_name = 'maxLength'
                if isinstance(field, serializers.ListField):
                    attr_name = 'maxItems'
                schema[attr_name] = v.limit_value
            elif isinstance(v, MinLengthValidator):
                attr_name = 'minLength'
                if isinstance(field, serializers.ListField):
                    attr_name = 'minItems'
                schema[attr_name] = v.limit_value
            elif isinstance(v, MaxValueValidator):
                schema['maximum'] = v.limit_value
            elif isinstance(v, MinValueValidator):
                schema['minimum'] = v.limit_value
            elif isinstance(v, DecimalValidator):
                if v.decimal_places:
                    schema['multipleOf'] = float('.' + (v.decimal_places - 1) * '0' + '1')
                if v.max_digits:
                    digits = v.max_digits
                    if v.decimal_places is not None and v.decimal_places > 0:
                        digits -= v.decimal_places
                    schema['maximum'] = int(digits * '9') + 1
                    schema['minimum'] = -schema['maximum']

    def _get_paginator(self):
        pagination_class = getattr(self.view, 'pagination_class', None)
        if pagination_class:
            return pagination_class()
        return None

    def map_parsers(self, path, method):
        return list(map(attrgetter('media_type'), self.view.parser_classes))

    def map_renderers(self, path, method):
        media_types = []
        for renderer in self.view.renderer_classes:
            # BrowsableAPIRenderer not relevant to OpenAPI spec
            if renderer == renderers.BrowsableAPIRenderer:
                continue
            media_types.append(renderer.media_type)
        return media_types

    def _get_serializer(self, method, path):
        view = self.view

        if not hasattr(view, 'get_serializer'):
            return None

        try:
            return view.get_serializer()
        except exceptions.APIException:
            warnings.warn('{}.get_serializer() raised an exception during '
                          'schema generation. Serializer fields will not be '
                          'generated for {} {}.'
                          .format(view.__class__.__name__, method, path))
            return None

    def _get_request_body(self, path, method):
        if method not in ('PUT', 'PATCH', 'POST'):
            return {}

        self.request_media_types = self.map_parsers(path, method)

        serializer = self._get_serializer(path, method)

        if not isinstance(serializer, serializers.Serializer):
            return {}

        content = self._map_serializer(serializer)
        # No required fields for PATCH
        if method == 'PATCH':
            content.pop('required', None)
        # No read_only fields for request.
        for name, schema in content['properties'].copy().items():
            if 'readOnly' in schema:
                del content['properties'][name]

        return {
            'content': {
                ct: {'schema': content}
                for ct in self.request_media_types
            }
        }

    def _get_responses(self, path, method):
        # TODO: Handle multiple codes and pagination classes.
        if method == 'DELETE':
            return {
                '204': {
                    'description': ''
                }
            }

        self.response_media_types = self.map_renderers(path, method)

        item_schema = {}
        serializer = self._get_serializer(path, method)

        if isinstance(serializer, serializers.Serializer):
            item_schema = self._map_serializer(serializer)
            # No write_only fields for response.
            for name, schema in item_schema['properties'].copy().items():
                if 'writeOnly' in schema:
                    del item_schema['properties'][name]
                    if 'required' in item_schema:
                        item_schema['required'] = [f for f in item_schema['required'] if f != name]

        if is_list_view(path, method, self.view):
            response_schema = {
                'type': 'array',
                'items': item_schema,
            }
            paginator = self._get_paginator()
            if paginator:
                response_schema = paginator.get_paginated_response_schema(response_schema)
        else:
            response_schema = item_schema

        return {
            '200': {
                'content': {
                    ct: {'schema': response_schema}
                    for ct in self.response_media_types
                },
                # description is a mandatory property,
                # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#responseObject
                # TODO: put something meaningful into it
                'description': ""
            }
        }
