from importlib import import_module

from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.core.urlresolvers import RegexURLPattern, RegexURLResolver
from django.utils import six
from django.utils.encoding import force_text

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


class SchemaGenerator(object):
    default_mapping = {
        'get': 'read',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }
    known_actions = (
        'create', 'read', 'retrieve', 'list',
        'update', 'partial_update', 'destroy'
    )

    def __init__(self, title=None, url=None, patterns=None, urlconf=None):
        assert coreapi, '`coreapi` must be installed for schema support.'

        if patterns is None and urlconf is not None:
            if isinstance(urlconf, six.string_types):
                urls = import_module(urlconf)
            else:
                urls = urlconf
            self.patterns = urls.urlpatterns
        elif patterns is None and urlconf is None:
            urls = import_module(settings.ROOT_URLCONF)
            self.patterns = urls.urlpatterns
        else:
            self.patterns = patterns

        if url and not url.endswith('/'):
            url += '/'

        self.title = title
        self.url = url
        self.endpoints = None

    def get_schema(self, request=None):
        if self.endpoints is None:
            self.endpoints = self.get_api_endpoints(self.patterns)

        links = []
        for path, method, category, action, callback in self.endpoints:
            view = callback.cls()
            for attr, val in getattr(callback, 'initkwargs', {}).items():
                setattr(view, attr, val)
            view.args = ()
            view.kwargs = {}
            view.format_kwarg = None

            actions = getattr(callback, 'actions', None)
            if actions is not None:
                if method == 'OPTIONS':
                    view.action = 'metadata'
                else:
                    view.action = actions.get(method.lower())

            if request is not None:
                view.request = clone_request(request, method)
                try:
                    view.check_permissions(view.request)
                except exceptions.APIException:
                    continue
            else:
                view.request = None

            link = self.get_link(path, method, callback, view)
            links.append((category, action, link))

        if not links:
            return None

        # Generate the schema content structure, eg:
        # {'users': {'list': Link()}}
        content = {}
        for category, action, link in links:
            if category is None:
                content[action] = link
            elif category in content:
                content[category][action] = link
            else:
                content[category] = {action: link}

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
                        action = self.get_action(path, method, callback)
                        category = self.get_category(path, method, callback, action)
                        endpoint = (path, method, category, action, callback)
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
            callback.cls().allowed_methods if method not in ('OPTIONS', 'HEAD')
        ]

    def get_action(self, path, method, callback):
        """
        Return a descriptive action string for the endpoint, eg. 'list'.
        """
        actions = getattr(callback, 'actions', self.default_mapping)
        return actions[method.lower()]

    def get_category(self, path, method, callback, action):
        """
        Return a descriptive category string for the endpoint, eg. 'users'.

        Examples of category/action pairs that should be generated for various
        endpoints:

        /users/                     [users][list], [users][create]
        /users/{pk}/                [users][read], [users][update], [users][destroy]
        /users/enabled/             [users][enabled]  (custom action)
        /users/{pk}/star/           [users][star]     (custom action)
        /users/{pk}/groups/         [groups][list], [groups][create]
        /users/{pk}/groups/{pk}/    [groups][read], [groups][update], [groups][destroy]
        """
        path_components = path.strip('/').split('/')
        path_components = [
            component for component in path_components
            if '{' not in component
        ]
        if action in self.known_actions:
            # Default action, eg "/users/", "/users/{pk}/"
            idx = -1
        else:
            # Custom action, eg "/users/{pk}/activate/", "/users/active/"
            idx = -2

        try:
            return path_components[idx]
        except IndexError:
            return None

    # Methods for generating each individual `Link` instance...

    def get_link(self, path, method, callback, view):
        """
        Return a `coreapi.Link` instance for the given endpoint.
        """
        fields = self.get_path_fields(path, method, callback, view)
        fields += self.get_serializer_fields(path, method, callback, view)
        fields += self.get_pagination_fields(path, method, callback, view)
        fields += self.get_filter_fields(path, method, callback, view)

        if fields and any([field.location in ('form', 'body') for field in fields]):
            encoding = self.get_encoding(path, method, callback, view)
        else:
            encoding = None

        if self.url and path.startswith('/'):
            path = path[1:]

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

        if not hasattr(view, 'get_serializer'):
            return []

        serializer = view.get_serializer()

        if isinstance(serializer, serializers.ListSerializer):
            return [coreapi.Field(name='data', location='body', required=True)]

        if not isinstance(serializer, serializers.Serializer):
            return []

        fields = []
        for field in serializer.fields.values():
            if field.read_only:
                continue
            required = field.required and method != 'PATCH'
            description = force_text(field.help_text) if field.help_text else ''
            field = coreapi.Field(
                name=field.source,
                location='form',
                required=required,
                description=description
            )
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
