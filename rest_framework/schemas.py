from importlib import import_module

import coreapi
import uritemplate
from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.utils import six

from rest_framework import exceptions
from rest_framework.request import clone_request
from rest_framework.views import APIView


class SchemaGenerator(object):
    default_mapping = {
        'get': 'read',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }

    def __init__(self, schema_title=None, patterns=None, urlconf=None):
        if patterns is None and urlconf is not None:
            if isinstance(urlconf, six.string_types):
                urls = import_module(urlconf)
            else:
                urls = urlconf
            patterns = urls.urlpatterns
        elif patterns is None and urlconf is None:
            urls = import_module(settings.ROOT_URLCONF)
            patterns = urls.urlpatterns

        self.schema_title = schema_title
        self.endpoints = self.get_api_endpoints(patterns)

    def get_schema(self, request=None):
        if request is None:
            endpoints = self.endpoints
        else:
            # Filter the list of endpoints to only include those that
            # the user has permission on.
            endpoints = []
            for key, link, callback in self.endpoints:
                method = link.action.upper()
                view = callback.cls()
                view.request = clone_request(request, method)
                try:
                    view.check_permissions(view.request)
                except exceptions.APIException:
                    pass
                else:
                    endpoints.append((key, link, callback))

        if not endpoints:
            return None

        # Generate the schema content structure, from the endpoints.
        # ('users', 'list'), Link -> {'users': {'list': Link()}}
        content = {}
        for key, link, callback in endpoints:
            insert_into = content
            for item in key[:1]:
                if item not in insert_into:
                    insert_into[item] = {}
                insert_into = insert_into[item]
            insert_into[key[-1]] = link

        # Return the schema document.
        return coreapi.Document(title=self.schema_title, content=content)

    def get_api_endpoints(self, patterns, prefix=''):
        """
        Return a list of all available API endpoints by inspecting the URL conf.
        """
        api_endpoints = []

        for pattern in patterns:
            path_regex = prefix + pattern.regex.pattern

            if isinstance(pattern, RegexURLPattern):
                path = self.get_path(path_regex)
                callback = pattern.callback
                if self.include_endpoint(path, callback):
                    for method in self.get_allowed_methods(callback):
                        key = self.get_key(path, method, callback)
                        link = self.get_link(path, method, callback)
                        endpoint = (key, link, callback)
                        api_endpoints.append(endpoint)

            elif isinstance(pattern, RegexURLResolver):
                nested_endpoints = self.get_api_endpoints(
                    patterns=pattern.url_patterns,
                    prefix=path_regex
                )
                api_endpoints.extend(nested_endpoints)

        return api_endpoints

    def get_path(self, path_regex):
        """
        Given a URL conf regex, return a URI template string.
        """
        path = simplify_regex(path_regex)
        path = path.replace('<', '{').replace('>', '}')
        return path

    def include_endpoint(self, path, callback):
        """
        Return True if the given endpoint should be included.
        """
        cls = getattr(callback, 'cls', None)
        if (cls is None) or not issubclass(cls, APIView):
            return False

        if path.endswith('.{format}') or path.endswith('.{format}/'):
            return False

        if path == '/':
            return False

        return True

    def get_allowed_methods(self, callback):
        """
        Return a list of the valid HTTP methods for this endpoint.
        """
        if hasattr(callback, 'actions'):
            return [method.upper() for method in callback.actions.keys()]

        return [
            method for method in
            callback.cls().allowed_methods if method != 'OPTIONS'
        ]

    def get_key(self, path, method, callback):
        """
        Return a tuple of strings, indicating the identity to use for a
        given endpoint. eg. ('users', 'list').
        """
        category = None
        for item in path.strip('/').split('/'):
            if '{' in item:
                break
            category = item

        actions = getattr(callback, 'actions', self.default_mapping)
        action = actions[method.lower()]

        if category:
            return (category, action)
        return (action,)

    def get_link(self, path, method, callback):
        """
        Return a `coreapi.Link` instance for the given endpoint.
        """
        view = callback.cls()
        fields = []

        for variable in uritemplate.variables(path):
            field = coreapi.Field(name=variable, location='path', required=True)
            fields.append(field)

        if method in ('PUT', 'PATCH', 'POST'):
            serializer_class = view.get_serializer_class()
            serializer = serializer_class()
            for field in serializer.fields.values():
                if field.read_only:
                    continue
                required = field.required and method != 'PATCH'
                field = coreapi.Field(name=field.source, location='form', required=required)
                fields.append(field)

        return coreapi.Link(url=path, action=method.lower(), fields=fields)
