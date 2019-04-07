import warnings

from django.db import models
from django.utils.encoding import force_text

from rest_framework import exceptions, serializers
from rest_framework.compat import uritemplate

from .generators import BaseSchemaGenerator
from .inspectors import ViewInspector
from .utils import get_pk_description, is_list_view

# Generator


class SchemaGenerator(BaseSchemaGenerator):

    def get_info(self):
        info = {
            'title': self.title,
            'version': 'TODO',
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
        prefix = self.determine_path_prefix(paths)

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            operation = view.schema.get_operation(path, method)
            subpath = '/' + path[len(prefix):]
            result.setdefault(subpath, {})
            result[subpath][method.lower()] = operation

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

    content_types = ['application/json']
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

        # TODO: Allow an attribute/method on the view to change that ID?
        # Avoid cyclic imports
        from rest_framework.generics import GenericAPIView

        method_name = getattr(self.view, 'action', method.lower())

        if is_list_view(path, method, self.view):
            action = 'List'
        elif method_name not in self.method_mapping:
            action = method_name
        else:
            action = self.method_mapping[method.lower()]

        # Try to deduce the ID from the view's model
        model = getattr(getattr(self.view, 'queryset', None), 'model', None)
        if model is not None:
            name = model.__name__

        # Try with the serializer class name
        elif isinstance(self.view, GenericAPIView):
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
            if name.endswith(action):  # ListView, UpdateAPIView, ThingDelete ...
                name = name[:-len(action)]

        if action == 'List' and not name.endswith('s'):  # ListThings instead of ListThing
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
                    description = force_text(model_field.help_text)
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

        pagination = getattr(view, 'pagination_class', None)
        if not pagination:
            return []

        paginator = view.pagination_class()
        return paginator.get_schema_operation_parameters(view)

    def _map_field(self, field):

        # Nested Serializers, `many` or not.
        if isinstance(field, serializers.ListSerializer):
            return {
                'type': 'array',
                'items': self._map_serializer(field.child)
            }
        if isinstance(field, serializers.Serializer):
            return {
                'type': 'object',
                'properties': self._map_serializer(field)
            }

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
            return {
                'type': 'array',
            }

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

        # Simplest cases, default to 'string' type:
        FIELD_CLASS_SCHEMA_TYPE = {
            serializers.BooleanField: 'boolean',
            serializers.DecimalField: 'number',
            serializers.FloatField: 'number',
            serializers.IntegerField: 'integer',

            serializers.JSONField: 'object',
            serializers.DictField: 'object',
        }
        return {'type': FIELD_CLASS_SCHEMA_TYPE.get(field.__class__, 'string')}

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

            properties[field.field_name] = schema
        return {
            'required': required,
            'properties': properties,
        }

    def _get_request_body(self, path, method):
        view = self.view

        if method not in ('PUT', 'PATCH', 'POST'):
            return {}

        if not hasattr(view, 'get_serializer'):
            return {}

        try:
            serializer = view.get_serializer()
        except exceptions.APIException:
            serializer = None
            warnings.warn('{}.get_serializer() raised an exception during '
                          'schema generation. Serializer fields will not be '
                          'generated for {} {}.'
                          .format(view.__class__.__name__, method, path))

        if not isinstance(serializer, serializers.Serializer):
            return {}

        content = self._map_serializer(serializer)
        # No required fields for PATCH
        if method == 'PATCH':
            del content['required']
        # No read_only fields for request.
        for name, schema in content['properties'].copy().items():
            if 'readOnly' in schema:
                del content['properties'][name]

        return {
            'content': {
                ct: {'schema': content}
                for ct in self.content_types
            }
        }

    def _get_responses(self, path, method):
        # TODO: Handle multiple codes.
        content = {}
        view = self.view
        if hasattr(view, 'get_serializer'):
            try:
                serializer = view.get_serializer()
            except exceptions.APIException:
                serializer = None
                warnings.warn('{}.get_serializer() raised an exception during '
                              'schema generation. Serializer fields will not be '
                              'generated for {} {}.'
                              .format(view.__class__.__name__, method, path))

            if isinstance(serializer, serializers.Serializer):
                content = self._map_serializer(serializer)
                # No write_only fields for response.
                for name, schema in content['properties'].copy().items():
                    if 'writeOnly' in schema:
                        del content['properties'][name]
                        content['required'] = [f for f in content['required'] if f != name]

        return {
            '200': {
                'content': {
                    ct: {'schema': content}
                    for ct in self.content_types
                }
            }
        }
