from importlib import import_module

from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.utils import six

from rest_framework import exceptions, serializers
from rest_framework.compat import coreapi, uritemplate, urlparse
from rest_framework.request import clone_request
from rest_framework.views import APIView


def as_query_fields(items):
    """
    Take a list of Fields and plain strings.
    Convert any pain strings into `location='query'` Field instances.
    """
    return [
        item if isinstance(item, coreapi.Field) else coreapi.Field(name=item, required=False, location='query')
        for item in items
    ]


def is_api_view(callback):
    """
    Return `True` if the given view callback is a REST framework view/viewset.
    """
    cls = getattr(callback, 'cls', None)
    return (cls is not None) and issubclass(cls, APIView)


def insert_into(target, keys, item):
    """
    Insert `item` into the nested dictionary `target`.

    For example:

        target = {}
        insert_into(target, ('users', 'list'), Link(...))
        insert_into(target, ('users', 'detail'), Link(...))
        assert target == {'users': {'list': Link(...), 'detail': Link(...)}}
    """
    for key in keys[:1]:
        if key not in target:
            target[key] = {}
        target = target[key]
    target[keys[-1]] = item


class SchemaGenerator(object):
    default_mapping = {
        'get': 'read',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }

    def __init__(self, title=None, url=None, patterns=None, urlconf=None):
        assert coreapi, '`coreapi` must be installed for schema support.'

        if patterns is None and urlconf is not None:
            if isinstance(urlconf, six.string_types):
                urls = import_module(urlconf)
            else:
                urls = urlconf
            patterns = urls.urlpatterns
        elif patterns is None and urlconf is None:
            urls = import_module(settings.ROOT_URLCONF)
            patterns = urls.urlpatterns

        if url and not url.endswith('/'):
            url += '/'

        self.title = title
        self.url = url
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
                view.format_kwarg = None
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
            insert_into(content, key, link)

        # Return the schema document.
        return coreapi.Document(title=self.title, content=content, url=self.url)

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
                if self.should_include_endpoint(path, callback):
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

    def should_include_endpoint(self, path, callback):
        """
        Return `True` if the given endpoint should be included.
        """
        if not is_api_view(callback):
            return False  # Ignore anything except REST framework views.

        if path.endswith('.{format}') or path.endswith('.{format}/'):
            return False  # Ignore .json style URLs.

        if path == '/':
            return False  # Ignore the root endpoint.

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

    # Methods for generating each individual `Link` instance...

    def get_link(self, path, method, callback):
        """
        Return a `coreapi.Link` instance for the given endpoint.
        """
        view = callback.cls()

        fields = self.get_path_fields(path, method, callback, view)
        fields += self.get_serializer_fields(path, method, callback, view)
        fields += self.get_pagination_fields(path, method, callback, view)
        fields += self.get_filter_fields(path, method, callback, view)

        if fields and any([field.location in ('form', 'body') for field in fields]):
            encoding = self.get_encoding(path, method, callback, view)
        else:
            encoding = None

        return coreapi.Link(
            url=urlparse.urljoin(self.url, path),
            action=method.lower(),
            encoding=encoding,
            fields=fields
        )

    def get_encoding(self, path, method, callback, view):
        """
        Return the 'encoding' parameter to use for a given endpoint.
        """
        # Core API supports the following request encodings over HTTP...
        supported_media_types = set((
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
        ))
        parser_classes = getattr(view, 'parser_classes', [])
        for parser_class in parser_classes:
            media_type = getattr(parser_class, 'media_type', None)
            if media_type in supported_media_types:
                return media_type
            # Raw binary uploads are supported with "application/octet-stream"
            if media_type == '*/*':
                return 'application/octet-stream'

        return None

    def get_path_fields(self, path, method, callback, view):
        """
        Return a list of `coreapi.Field` instances corresponding to any
        templated path variables.
        """
        fields = []

        for variable in uritemplate.variables(path):
            field = coreapi.Field(name=variable, location='path', required=True)
            fields.append(field)

        return fields

    def get_serializer_fields(self, path, method, callback, view):
        """
        Return a list of `coreapi.Field` instances corresponding to any
        request body input, as determined by the serializer class.
        """
        if method not in ('PUT', 'PATCH', 'POST'):
            return []

        if not hasattr(view, 'get_serializer_class'):
            return []

        fields = []

        serializer_class = view.get_serializer_class()
        serializer = serializer_class()

        if isinstance(serializer, serializers.ListSerializer):
            return coreapi.Field(name='data', location='body', required=True)

        if not isinstance(serializer, serializers.Serializer):
            return []

        for field in serializer.fields.values():
            if field.read_only:
                continue
            required = field.required and method != 'PATCH'
            field = coreapi.Field(name=field.source, location='form', required=required)
            fields.append(field)

        return fields

    def get_pagination_fields(self, path, method, callback, view):
        if method != 'GET':
            return []

        if hasattr(callback, 'actions') and ('list' not in callback.actions.values()):
            return []

        if not getattr(view, 'pagination_class', None):
            return []

        paginator = view.pagination_class()
        return as_query_fields(paginator.get_fields(view))

    def get_filter_fields(self, path, method, callback, view):
        if method != 'GET':
            return []

        if hasattr(callback, 'actions') and ('list' not in callback.actions.values()):
            return []

        if not hasattr(view, 'filter_backends'):
            return []

        fields = []
        for filter_backend in view.filter_backends:
            fields += as_query_fields(filter_backend().get_fields(view))
        return fields
