import inspect
import warnings
from decimal import Decimal
from uuid import UUID
from datetime import datetime, date

from rest_framework import authentication
from rest_framework.settings import api_settings

VALID_TYPES = ['integer', 'number', 'string', 'boolean']

TYPE_MAPPING = {
    float: {'type': 'number', 'format': 'float'},
    bool: {'type': 'boolean'},
    str: {'type': 'string'},
    bytes: {'type': 'string', 'format': 'binary'},  # or byte?
    int: {'type': 'integer'},
    UUID: {'type': 'string', 'format': 'uuid'},
    Decimal: {'type': 'number', 'format': 'double'},
    datetime: {'type': 'string', 'format': 'date-time'},
    date: {'type': 'string', 'format': 'date'},
    None: {},
    type(None): {},
}


class OpenApiAuthenticationScheme:
    authentication_class = None
    name = None
    schema = None


class SessionAuthenticationScheme(OpenApiAuthenticationScheme):
    authentication_class = authentication.SessionAuthentication
    name = 'cookieAuth'
    schema = {
        'type': 'apiKey',
        'in': 'cookie',
        'name': 'Session',
    }


class BasicAuthenticationScheme(OpenApiAuthenticationScheme):
    authentication_class = authentication.BasicAuthentication
    name = 'basicAuth'
    schema = {
        'type': 'http',
        'scheme': 'basic',
    }


class TokenAuthenticationScheme(OpenApiAuthenticationScheme):
    authentication_class = authentication.TokenAuthentication
    name = 'tokenAuth'
    schema = {
        'type': 'http',
        'scheme': 'bearer',
        'bearerFormat': 'Token',
    }


class PolymorphicResponse:
    def __init__(self, serializers, resource_type_field_name):
        self.serializers = serializers
        self.resource_type_field_name = resource_type_field_name


class OpenApiSchemaBase:
    """ reusable base class for objects that can be translated to a schema """
    def to_schema(self):
        raise NotImplementedError('translation to schema required.')


class QueryParameter(OpenApiSchemaBase):
    def __init__(self, name, description='', required=False, type=str):
        self.name = name
        self.description = description
        self.required = required
        self.type = type

    def to_schema(self):
        if self.type not in TYPE_MAPPING:
            warnings.warn('{} not a mappable type'.format(self.type))
        return {
            'name': self.name,
            'in': 'query',
            'description': self.description,
            'required': self.required,
            'schema': TYPE_MAPPING.get(self.type)
        }


def extend_schema(
        operation=None,
        extra_parameters=None,
        responses=None,
        request=None,
        auth=None,
        description=None,
):
    """
    TODO some heavy explaining

    :param operation:
    :param extra_parameters:
    :param responses:
    :param request:
    :param auth:
    :param description:
    :return:
    """

    def decorator(f):
        class ExtendedSchema(api_settings.DEFAULT_SCHEMA_CLASS):
            def get_operation(self, path, method):
                if operation:
                    return operation
                return super().get_operation(path, method)

            def get_extra_parameters(self, path, method):
                if extra_parameters:
                    return [
                        p.to_schema() if isinstance(p, OpenApiSchemaBase) else p for p in extra_parameters
                    ]
                return super().get_extra_parameters(path, method)

            def get_auth(self, path, method):
                if auth:
                    return auth
                return super().get_auth(path, method)

            def get_request_serializer(self, path, method):
                if request:
                    return request
                return super().get_request_serializer(path, method)

            def get_response_serializers(self, path, method):
                if responses:
                    return responses
                return super().get_response_serializers(path, method)

            def get_description(self, path, method):
                if description:
                    return description
                return super().get_description(path, method)

        if inspect.isclass(f):
            class ExtendedView(f):
                schema = ExtendedSchema()

            return ExtendedView
        elif callable(f):
            # custom actions have kwargs in their context, others don't. create it so our create_view
            # implementation can overwrite the default schema
            if not hasattr(f, 'kwargs'):
                f.kwargs = {}

            # this simulates what @action is actually doing. somewhere along the line in this process
            # the schema is picked up from kwargs and used. it's involved my dear friends.
            f.kwargs['schema'] = ExtendedSchema()
            return f
        else:
            return f

    return decorator
