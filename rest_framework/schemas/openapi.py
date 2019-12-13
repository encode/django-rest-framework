import inspect
import re
import typing
import warnings
from operator import attrgetter
from urllib.parse import urljoin
from uuid import UUID

from django.core.validators import (
    DecimalValidator, EmailValidator, MaxLengthValidator, MaxValueValidator,
    MinLengthValidator, MinValueValidator, RegexValidator, URLValidator
)
from django.db import models
from django.utils.encoding import force_str
from django.utils.module_loading import import_string

from rest_framework import exceptions, permissions, renderers, serializers
from rest_framework.compat import uritemplate
from rest_framework.fields import _UnvalidatedField, empty
from rest_framework.schemas.openapi_utils import (
    TYPE_MAPPING, PolymorphicResponse
)
from rest_framework.settings import api_settings

from .generators import BaseSchemaGenerator
from .inspectors import ViewInspector
from .utils import get_pk_description, is_list_view

AUTHENTICATION_SCHEMES = {
    cls.authentication_class: cls
    for cls in [import_string(cls) for cls in api_settings.SCHEMA_AUTHENTICATION_CLASSES]
}


class ComponentRegistry:
    def __init__(self):
        self.schemas = {}
        self.security_schemes = {}

    def get_components(self):
        return {
            'securitySchemes': self.security_schemes,
            'schemas': self.schemas,
        }


class SchemaGenerator(BaseSchemaGenerator):
    def __init__(self, *args, **kwargs):
        self.registry = ComponentRegistry()
        super().__init__(*args, **kwargs)

    def create_view(self, callback, method, request=None):
        """
        customized create_view which is called when all routes are traversed. part of this
        is instatiating views with default params. in case of custom routes (@action) the
        custom AutoSchema is injected properly through 'initkwargs' on view. However, when
        decorating plain views like retrieve, this initialization logic is not running.
        Therefore forcefully set the schema if @extend_schema decorator was used.
        """
        view = super().create_view(callback, method, request)

        # circumvent import issues by locally importing
        from rest_framework.views import APIView
        from rest_framework.viewsets import GenericViewSet, ViewSet

        if isinstance(view, GenericViewSet) or isinstance(view, ViewSet):
            action = getattr(view, view.action)
        elif isinstance(view, APIView):
            action = getattr(view, method.lower())
        else:
            raise RuntimeError('not supported subclass. Must inherit from APIView')

        if hasattr(action, 'kwargs') and 'schema' in action.kwargs:
            # might already be properly set in case of @action but overwrite for all cases
            view.schema = action.kwargs['schema']

        return view

    def parse(self, request=None):
        result = {}

        paths, view_endpoints = self._get_paths_and_endpoints(request)

        # Only generate the path prefix for paths that will be included
        if not paths:
            return None

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            # keep reference to schema as every access yields a fresh object (descriptor )
            schema = view.schema
            schema.init(self.registry)
            operation = schema.get_operation(path, method)
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

        schema = {
            'openapi': '3.0.2',
            'servers': [
                {'url': self.url or 'http://127.0.0.1:8000'},
            ],
            'info': {
                'title': self.title or '',
                'version': self.version or '0.0.0',  # fallback to prevent invalid schema
                'description': self.description or '',
            },
            'paths': self.parse(None if public else request),
            'components': self.registry.get_components(),
        }
        return schema


class AutoSchema(ViewInspector):

    request_media_types = []
    response_media_types = []

    method_mapping = {
        'get': 'retrieve',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }

    def init(self, registry):
        self.registry = registry

    def get_operation(self, path, method):
        operation = {}

        operation['operationId'] = self.get_operation_id(path, method)
        operation['description'] = self.get_description(path, method)
        operation['parameters'] = sorted(
            [
                *self._get_path_parameters(path, method),
                *self._get_filter_parameters(path, method),
                *self._get_pagination_parameters(path, method),
                *self.get_extra_parameters(path, method),
            ],
            key=lambda p: p.get('name')
        )

        tags = self.get_tags(path, method)
        if tags:
            operation['tags'] = tags

        request_body = self._get_request_body(path, method)
        if request_body:
            operation['requestBody'] = request_body

        auth = self.get_auth(path, method)
        if auth:
            operation['security'] = auth

        self.response_media_types = self.map_renderers(path, method)

        operation['responses'] = self._get_response_bodies(path, method)

        return operation

    def get_extra_parameters(self, path, method):
        """ override this for custom behaviour """
        return []

    def get_description(self, path, method):
        """ override this for custom behaviour """
        action_or_method = getattr(self.view, getattr(self.view, 'action', method.lower()), None)
        view_doc = inspect.getdoc(self.view) or ''
        action_doc = inspect.getdoc(action_or_method) or ''
        return action_doc or view_doc

    def get_auth(self, path, method):
        """ override this for custom behaviour """
        auth = []
        if hasattr(self.view, 'authentication_classes'):
            auth = [
                self.resolve_authentication(method, ac) for ac in self.view.authentication_classes
            ]
        if hasattr(self.view, 'permission_classes'):
            perms = self.view.permission_classes
            if permissions.AllowAny in perms:
                auth.append({})
            elif permissions.IsAuthenticatedOrReadOnly in perms and method not in ('PUT', 'PATCH', 'POST'):
                auth.append({})
        return auth

    def get_request_serializer(self, path, method):
        """ override this for custom behaviour """
        return self._get_serializer(path, method)

    def get_response_serializers(self, path, method):
        """ override this for custom behaviour """
        return self._get_serializer(path, method)

    def get_tags(self, path, method):
        """ override this for custom behaviour """
        tokenized_path = self._tokenize_path(path)
        # use first non-parameter path part as tag
        return tokenized_path[:1]

    def get_operation_id(self, path, method):
        """ override this for custom behaviour """
        tokenized_path = self._tokenize_path(path)
        # replace dashes as they can be problematic later in code generation
        tokenized_path = [t.replace('-', '_') for t in tokenized_path]

        if is_list_view(path, method, self.view):
            action = 'list'
        else:
            action = self.method_mapping[method.lower()]

        return '_'.join(tokenized_path + [action])

    def _tokenize_path(self, path):
        # remove path prefix
        path = re.sub(
            pattern=api_settings.SCHEMA_PATH_PREFIX,
            repl='',
            string=path,
            flags=re.IGNORECASE
        )
        # cleanup and tokenize remaining parts.
        path = path.rstrip('/').lstrip('/').split('/')
        # remove path variables and empty tokens
        return [t for t in path if t and not t.startswith('{')]

    def _get_path_parameters(self, path, method):
        """
        Return a list of parameters from templated path variables.
        """
        assert uritemplate, '`uritemplate` must be installed for OpenAPI schema support.'

        model = getattr(getattr(self.view, 'queryset', None), 'model', None)
        parameters = []

        for variable in uritemplate.variables(path):
            description = ''
            schema = TYPE_MAPPING[str]

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

                # TODO are there more relevant PK base classes?
                if isinstance(model_field, models.IntegerField):
                    schema = TYPE_MAPPING[int]
                elif isinstance(model_field, models.UUIDField):
                    schema = TYPE_MAPPING[UUID]

            parameter = {
                "name": variable,
                "in": "path",
                "required": True,
                "description": description,
                'schema': schema,
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

    def _map_field(self, method, field):
        # Nested Serializers, `many` or not.
        if isinstance(field, serializers.ListSerializer):
            return {
                'type': 'array',
                'items': self.resolve_serializer(method, field.child)
            }
        if isinstance(field, serializers.Serializer):
            data = self.resolve_serializer(method, field, nested=True)
            data['type'] = 'object'
            return data

        # Related fields.
        if isinstance(field, serializers.ManyRelatedField):
            return {
                'type': 'array',
                'items': self._map_field(method, field.child_relation)
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

        if isinstance(field, serializers.ListField):
            mapping = {
                'type': 'array',
                'items': {},
            }
            if not isinstance(field.child, _UnvalidatedField):
                map_field = self._map_field(method, field.child)
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

        if isinstance(field, serializers.SerializerMethodField):
            method = getattr(field.parent, field.method_name)
            return self._map_type_hint(method)

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

    def _map_serializer(self, method, serializer, nested=False):
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

            schema = self._map_field(method, field)
            if field.read_only:
                schema['readOnly'] = True
            if field.write_only:
                schema['writeOnly'] = True
            if field.allow_null:
                schema['nullable'] = True
            if field.default and field.default != empty and not callable(field.default):
                schema['default'] = field.default
            if field.help_text:
                schema['description'] = str(field.help_text)
            self._map_field_validators(field, schema)

            properties[field.field_name] = schema

        result = {
            'properties': properties
        }
        if required and method != 'PATCH':
            result['required'] = required

        return result

    def _map_field_validators(self, field, schema):
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

    def _map_type_hint(self, method, hint=None):
        if not hint:
            hint = typing.get_type_hints(method).get('return')

        if hint in TYPE_MAPPING:
            return TYPE_MAPPING[hint]
        elif hint.__origin__ is typing.Union:
            sub_hints = [
                self._map_type_hint(method, sub_hint)
                for sub_hint in hint.__args__ if sub_hint is not type(None)  # noqa
            ]
            if type(None) in hint.__args__ and len(sub_hints) == 1:
                return {**sub_hints[0], 'nullable': True}
            elif type(None) in hint.__args__:
                return {'oneOf': [{**sub_hint, 'nullable': True} for sub_hint in sub_hints]}
            else:
                return {'oneOf': sub_hints}
        else:
            warnings.warn(
                'type hint for SerializerMethodField function "{}" is unknown. '
                'defaulting to string.'.format(method.__name__)
            )
            return {'type': 'string'}

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
            warnings.warn(
                '{}.get_serializer() raised an exception during '
                'schema generation. Serializer fields will not be '
                'generated for {} {}.'.format(view.__class__.__name__, method, path)
            )
            return None

    def _get_request_body(self, path, method):
        if method not in ('PUT', 'PATCH', 'POST'):
            return {}

        request_media_types = self.map_parsers(path, method)

        serializer = self._get_serializer(path, method)

        if isinstance(serializer, serializers.Serializer):
            schema = self.resolve_serializer(method, serializer)
        else:
            warnings.warn(
                'could not resolve request body for {} {}. defaulting to generic '
                'free-form object. (maybe annotate a Serializer class?)'.format(method, path)
            )
            schema = {
                'type': 'object',
                'additionalProperties': {},  # https://github.com/swagger-api/swagger-codegen/issues/1318
                'description': 'Unspecified request body',
            }

        # serializer has no fields so skip content enumeration
        if not schema:
            return {}

        return {
            'content': {mt: {'schema': schema} for mt in request_media_types}
        }

    def _get_response_bodies(self, path, method):
        response_serializers = self.get_response_serializers(path, method)

        if isinstance(response_serializers, serializers.Serializer) or isinstance(response_serializers, PolymorphicResponse):
            if method == 'DELETE':
                return {'204': {'description': 'No response body'}}
            return {'200': self._get_response_for_code(path, method, response_serializers)}
        elif isinstance(response_serializers, dict):
            # custom handling for overriding default return codes with @extend_schema
            return {
                code: self._get_response_for_code(path, method, serializer)
                for code, serializer in response_serializers.items()
            }
        else:
            warnings.warn(
                'could not resolve response for {} {}. defaulting '
                'to generic free-form object.'.format(method, path)
            )
            schema = {
                'type': 'object',
                'description': 'Unspecified response body',
            }
            return {'200': self._get_response_for_code(path, method, schema)}

    def _get_response_for_code(self, path, method, serializer_instance):
        if not serializer_instance:
            return {'description': 'No response body'}
        elif isinstance(serializer_instance, serializers.Serializer):
            schema = self.resolve_serializer(method, serializer_instance)
            if not schema:
                return {'description': 'No response body'}
        elif isinstance(serializer_instance, PolymorphicResponse):
            # custom handling for @extend_schema's injection of polymorphic responses
            schemas = []

            for serializer in serializer_instance.serializers:
                assert isinstance(serializer, serializers.Serializer)
                schema_option = self.resolve_serializer(method, serializer)
                if schema_option:
                    schemas.append(schema_option)

            schema = {
                'oneOf': schemas,
                'discriminator': {
                    'propertyName': serializer_instance.resource_type_field_name
                }
            }
        elif isinstance(serializer_instance, dict):
            # bypass processing and use given schema directly
            schema = serializer_instance
        else:
            raise ValueError('Serializer type unsupported')

        if is_list_view(path, method, self.view):
            schema = {
                'type': 'array',
                'items': schema,
            }
            paginator = self._get_paginator()
            if paginator:
                schema = paginator.get_paginated_response_schema(schema)

        return {
            'content': {
                mt: {'schema': schema} for mt in self.response_media_types
            },
            # Description is required by spec, but descriptions for each response code don't really
            # fit into our model. Description is therefore put into the higher level slots.
            # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#responseObject
            'description': ''
        }

    def _get_serializer_name(self, method, serializer, nested):
        name = serializer.__class__.__name__

        if name.endswith('Serializer'):
            name = name[:-10]
        if method == 'PATCH' and not serializer.read_only:  # TODO maybe even use serializer.partial
            name = 'Patched' + name

        return name

    def resolve_authentication(self, method, authentication):
        if authentication not in AUTHENTICATION_SCHEMES:
            raise ValueError()

        auth_scheme = AUTHENTICATION_SCHEMES.get(authentication)

        if not auth_scheme:
            raise ValueError('no auth scheme registered for {}'.format(authentication.__name__))

        if auth_scheme.name not in self.registry.security_schemes:
            self.registry.security_schemes[auth_scheme.name] = auth_scheme.schema

        return {auth_scheme.name: []}

    def resolve_serializer(self, method, serializer, nested=False):
        name = self._get_serializer_name(method, serializer, nested)

        if name not in self.registry.schemas:
            # add placeholder to prevent recursion loop
            self.registry.schemas[name] = None

            mapped = self._map_serializer(method, serializer, nested)
            # empty serializer - usually a transactional serializer.
            # no need to put it explicitly in the spec
            if not mapped['properties']:
                del self.registry.schemas[name]
                return {}
            else:
                self.registry.schemas[name] = mapped

        return {'$ref': '#/components/schemas/{}'.format(name)}


class PolymorphicAutoSchema(AutoSchema):
    """

    """
    def resolve_serializer(self, method, serializer, nested=False):
        try:
            from rest_polymorphic.serializers import PolymorphicSerializer
        except ImportError:
            warnings.warn('rest_polymorphic package required for PolymorphicAutoSchema')
            raise

        if isinstance(serializer, PolymorphicSerializer):
            return self._resolve_polymorphic_serializer(method, serializer, nested)
        else:
            return super().resolve_serializer(method, serializer, nested)

    def _resolve_polymorphic_serializer(self, method, serializer, nested):
        polymorphic_names = []

        for poly_model, poly_serializer in serializer.model_serializer_mapping.items():
            name = self._get_serializer_name(method, poly_serializer, nested)

            if name not in self.registry.schemas:
                # add placeholder to prevent recursion loop
                self.registry.schemas[name] = None
                # append the type field to serializer fields
                mapped = self._map_serializer(method, poly_serializer, nested)
                mapped['properties'][serializer.resource_type_field_name] = {'type': 'string'}
                self.registry.schemas[name] = mapped

            polymorphic_names.append(name)

        return {
            'oneOf': [
                {'$ref': '#/components/schemas/{}'.format(name)} for name in polymorphic_names
            ],
            'discriminator': {
                'propertyName': serializer.resource_type_field_name
            }
        }
