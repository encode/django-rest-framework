import re
from collections import OrderedDict
from importlib import import_module

from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.utils import six
from django.utils.encoding import force_text, smart_text

from rest_framework import exceptions, renderers, serializers
from rest_framework.compat import (
    RegexURLPattern, RegexURLResolver, coreapi, uritemplate, urlparse
)
from rest_framework.request import clone_request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils import formatting
from rest_framework.utils.field_mapping import ClassLookupDict
from rest_framework.utils.model_meta import _get_pk
from rest_framework.views import APIView


header_regex = re.compile('^[a-zA-Z][0-9A-Za-z_]*:')

types_lookup = ClassLookupDict({
    serializers.Field: 'string',
    serializers.IntegerField: 'integer',
    serializers.FloatField: 'number',
    serializers.DecimalField: 'number',
    serializers.BooleanField: 'boolean',
    serializers.FileField: 'file',
    serializers.MultipleChoiceField: 'array',
    serializers.ManyRelatedField: 'array',
    serializers.Serializer: 'object',
    serializers.ListSerializer: 'array'
})


def common_path(paths):
    split_paths = [path.strip('/').split('/') for path in paths]
    s1 = min(split_paths)
    s2 = max(split_paths)
    common = s1
    for i, c in enumerate(s1):
        if c != s2[i]:
            common = s1[:i]
            break
    return '/' + '/'.join(common)


def get_pk_name(model):
    meta = model._meta.concrete_model._meta
    return _get_pk(meta).name


def is_api_view(callback):
    """
    Return `True` if the given view callback is a REST framework view/viewset.
    """
    cls = getattr(callback, 'cls', None)
    return (cls is not None) and issubclass(cls, APIView)


def insert_into(target, keys, value):
    """
    Nested dictionary insertion.

    >>> example = {}
    >>> insert_into(example, ['a', 'b', 'c'], 123)
    >>> example
    {'a': {'b': {'c': 123}}}
    """
    for key in keys[:-1]:
        if key not in target:
            target[key] = {}
        target = target[key]
    target[keys[-1]] = value


def is_custom_action(action):
    return action not in set([
        'retrieve', 'list', 'create', 'update', 'partial_update', 'destroy'
    ])


def is_list_view(path, method, view):
    """
    Return True if the given path/method appears to represent a list view.
    """
    if hasattr(view, 'action'):
        # Viewsets have an explicitly defined action, which we can inspect.
        return view.action == 'list'

    if method.lower() != 'get':
        return False
    path_components = path.strip('/').split('/')
    if path_components and '{' in path_components[-1]:
        return False
    return True


def endpoint_ordering(endpoint):
    path, method, callback = endpoint
    method_priority = {
        'GET': 0,
        'POST': 1,
        'PUT': 2,
        'PATCH': 3,
        'DELETE': 4
    }.get(method, 5)
    return (path, method_priority)


class EndpointInspector(object):
    """
    A class to determine the available API endpoints that a project exposes.
    """
    def __init__(self, patterns=None, urlconf=None):
        if patterns is None:
            if urlconf is None:
                # Use the default Django URL conf
                urlconf = settings.ROOT_URLCONF

            # Load the given URLconf module
            if isinstance(urlconf, six.string_types):
                urls = import_module(urlconf)
            else:
                urls = urlconf
            patterns = urls.urlpatterns

        self.patterns = patterns

    def get_api_endpoints(self, patterns=None, prefix=''):
        """
        Return a list of all available API endpoints by inspecting the URL conf.
        """
        if patterns is None:
            patterns = self.patterns

        api_endpoints = []

        for pattern in patterns:
            path_regex = prefix + pattern.regex.pattern
            if isinstance(pattern, RegexURLPattern):
                path = self.get_path_from_regex(path_regex)
                callback = pattern.callback
                if self.should_include_endpoint(path, callback):
                    for method in self.get_allowed_methods(callback):
                        endpoint = (path, method, callback)
                        api_endpoints.append(endpoint)

            elif isinstance(pattern, RegexURLResolver):
                nested_endpoints = self.get_api_endpoints(
                    patterns=pattern.url_patterns,
                    prefix=path_regex
                )
                api_endpoints.extend(nested_endpoints)

        api_endpoints = sorted(api_endpoints, key=endpoint_ordering)

        return api_endpoints

    def get_path_from_regex(self, path_regex):
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


class SchemaGenerator(object):
    # Map HTTP methods onto actions.
    default_mapping = {
        'get': 'retrieve',
        'post': 'create',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }
    endpoint_inspector_cls = EndpointInspector

    # Map the method names we use for viewset actions onto external schema names.
    # These give us names that are more suitable for the external representation.
    # Set by 'SCHEMA_COERCE_METHOD_NAMES'.
    coerce_method_names = None

    # 'pk' isn't great as an externally exposed name for an identifier,
    # so by default we prefer to use the actual model field name for schemas.
    # Set by 'SCHEMA_COERCE_PATH_PK'.
    coerce_path_pk = None

    def __init__(self, title=None, url=None, patterns=None, urlconf=None):
        assert coreapi, '`coreapi` must be installed for schema support.'

        if url and not url.endswith('/'):
            url += '/'

        self.coerce_method_names = api_settings.SCHEMA_COERCE_METHOD_NAMES
        self.coerce_path_pk = api_settings.SCHEMA_COERCE_PATH_PK

        self.patterns = patterns
        self.urlconf = urlconf
        self.title = title
        self.url = url
        self.endpoints = None

    def get_schema(self, request=None):
        """
        Generate a `coreapi.Document` representing the API schema.
        """
        if self.endpoints is None:
            inspector = self.endpoint_inspector_cls(self.patterns, self.urlconf)
            self.endpoints = inspector.get_api_endpoints()

        links = self.get_links(request)
        if not links:
            return None
        return coreapi.Document(title=self.title, url=self.url, content=links)

    def get_links(self, request=None):
        """
        Return a dictionary containing all the links that should be
        included in the API schema.
        """
        links = OrderedDict()

        # Generate (path, method, view) given (path, method, callback).
        paths = []
        view_endpoints = []
        for path, method, callback in self.endpoints:
            view = self.create_view(callback, method, request)
            if getattr(view, 'exclude_from_schema', False):
                continue
            path = self.coerce_path(path, method, view)
            paths.append(path)
            view_endpoints.append((path, method, view))

        # Only generate the path prefix for paths that will be included
        prefix = self.determine_path_prefix(paths)

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            link = self.get_link(path, method, view)
            subpath = path[len(prefix):]
            keys = self.get_keys(subpath, method, view)
            insert_into(links, keys, link)
        return links

    # Methods used when we generate a view instance from the raw callback...

    def determine_path_prefix(self, paths):
        """
        Given a list of all paths, return the common prefix which should be
        discounted when generating a schema structure.

        This will be the longest common string that does not include that last
        component of the URL, or the last component before a path parameter.

        For example:

        /api/v1/users/
        /api/v1/users/{pk}/

        The path prefix is '/api/v1/'
        """
        prefixes = []
        for path in paths:
            components = path.strip('/').split('/')
            initial_components = []
            for component in components:
                if '{' in component:
                    break
                initial_components.append(component)
            prefix = '/'.join(initial_components[:-1])
            if not prefix:
                # We can just break early in the case that there's at least
                # one URL that doesn't have a path prefix.
                return '/'
            prefixes.append('/' + prefix + '/')
        return common_path(prefixes)

    def create_view(self, callback, method, request=None):
        """
        Given a callback, return an actual view instance.
        """
        view = callback.cls()
        for attr, val in getattr(callback, 'initkwargs', {}).items():
            setattr(view, attr, val)
        view.args = ()
        view.kwargs = {}
        view.format_kwarg = None
        view.request = None
        view.action_map = getattr(callback, 'actions', None)

        actions = getattr(callback, 'actions', None)
        if actions is not None:
            if method == 'OPTIONS':
                view.action = 'metadata'
            else:
                view.action = actions.get(method.lower())

        if request is not None:
            view.request = clone_request(request, method)

        return view

    def has_view_permissions(self, path, method, view):
        """
        Return `True` if the incoming request has the correct view permissions.
        """
        if view.request is None:
            return True

        try:
            view.check_permissions(view.request)
        except exceptions.APIException:
            return False
        return True

    def coerce_path(self, path, method, view):
        """
        Coerce {pk} path arguments into the name of the model field,
        where possible. This is cleaner for an external representation.
        (Ie. "this is an identifier", not "this is a database primary key")
        """
        if not self.coerce_path_pk or '{pk}' not in path:
            return path
        model = getattr(getattr(view, 'queryset', None), 'model', None)
        if model:
            field_name = get_pk_name(model)
        else:
            field_name = 'id'
        return path.replace('{pk}', '{%s}' % field_name)

    # Methods for generating each individual `Link` instance...

    def get_link(self, path, method, view):
        """
        Return a `coreapi.Link` instance for the given endpoint.
        """
        fields = self.get_path_fields(path, method, view)
        fields += self.get_serializer_fields(path, method, view)
        fields += self.get_pagination_fields(path, method, view)
        fields += self.get_filter_fields(path, method, view)

        if fields and any([field.location in ('form', 'body') for field in fields]):
            encoding = self.get_encoding(path, method, view)
        else:
            encoding = None

        description = self.get_description(path, method, view)

        if self.url and path.startswith('/'):
            path = path[1:]

        return coreapi.Link(
            url=urlparse.urljoin(self.url, path),
            action=method.lower(),
            encoding=encoding,
            fields=fields,
            description=description
        )

    def get_description(self, path, method, view):
        """
        Determine a link description.

        This will be based on the method docstring if one exists,
        or else the class docstring.
        """
        method_name = getattr(view, 'action', method.lower())
        method_docstring = getattr(view, method_name, None).__doc__
        if method_docstring:
            # An explicit docstring on the method or action.
            return formatting.dedent(smart_text(method_docstring))

        description = view.get_view_description()
        lines = [line.strip() for line in description.splitlines()]
        current_section = ''
        sections = {'': ''}

        for line in lines:
            if header_regex.match(line):
                current_section, seperator, lead = line.partition(':')
                sections[current_section] = lead.strip()
            else:
                sections[current_section] += line + '\n'

        header = getattr(view, 'action', method.lower())
        if header in sections:
            return sections[header].strip()
        if header in self.coerce_method_names:
            if self.coerce_method_names[header] in sections:
                return sections[self.coerce_method_names[header]].strip()
        return sections[''].strip()

    def get_encoding(self, path, method, view):
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

    def get_path_fields(self, path, method, view):
        """
        Return a list of `coreapi.Field` instances corresponding to any
        templated path variables.
        """
        fields = []

        for variable in uritemplate.variables(path):
            field = coreapi.Field(name=variable, location='path', required=True)
            fields.append(field)

        return fields

    def get_serializer_fields(self, path, method, view):
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
            return [
                coreapi.Field(
                    name='data',
                    location='body',
                    required=True,
                    type='array'
                )
            ]

        if not isinstance(serializer, serializers.Serializer):
            return []

        fields = []
        for field in serializer.fields.values():
            if field.read_only or isinstance(field, serializers.HiddenField):
                continue

            required = field.required and method != 'PATCH'
            description = force_text(field.help_text) if field.help_text else ''
            field = coreapi.Field(
                name=field.field_name,
                location='form',
                required=required,
                description=description,
                type=types_lookup[field]
            )
            fields.append(field)

        return fields

    def get_pagination_fields(self, path, method, view):
        if not is_list_view(path, method, view):
            return []

        if not getattr(view, 'pagination_class', None):
            return []

        paginator = view.pagination_class()
        return paginator.get_schema_fields(view)

    def get_filter_fields(self, path, method, view):
        if not is_list_view(path, method, view):
            return []

        if not getattr(view, 'filter_backends', None):
            return []

        fields = []
        for filter_backend in view.filter_backends:
            fields += filter_backend().get_schema_fields(view)
        return fields

    # Method for generating the link layout....

    def get_keys(self, subpath, method, view):
        """
        Return a list of keys that should be used to layout a link within
        the schema document.

        /users/                   ("users", "list"), ("users", "create")
        /users/{pk}/              ("users", "read"), ("users", "update"), ("users", "delete")
        /users/enabled/           ("users", "enabled")  # custom viewset list action
        /users/{pk}/star/         ("users", "star")     # custom viewset detail action
        /users/{pk}/groups/       ("users", "groups", "list"), ("users", "groups", "create")
        /users/{pk}/groups/{pk}/  ("users", "groups", "read"), ("users", "groups", "update"), ("users", "groups", "delete")
        """
        if hasattr(view, 'action'):
            # Viewsets have explicitly named actions.
            action = view.action
        else:
            # Views have no associated action, so we determine one from the method.
            if is_list_view(subpath, method, view):
                action = 'list'
            else:
                action = self.default_mapping[method.lower()]

        named_path_components = [
            component for component
            in subpath.strip('/').split('/')
            if '{' not in component
        ]

        if is_custom_action(action):
            # Custom action, eg "/users/{pk}/activate/", "/users/active/"
            if len(view.action_map) > 1:
                action = self.default_mapping[method.lower()]
                if action in self.coerce_method_names:
                    action = self.coerce_method_names[action]
                return named_path_components + [action]
            else:
                return named_path_components[:-1] + [action]

        if action in self.coerce_method_names:
            action = self.coerce_method_names[action]

        # Default action, eg "/users/", "/users/{pk}/"
        return named_path_components + [action]


def get_schema_view(title=None, url=None, renderer_classes=None):
    """
    Return a schema view.
    """
    generator = SchemaGenerator(title=title, url=url)
    if renderer_classes is None:
        if renderers.BrowsableAPIRenderer in api_settings.DEFAULT_RENDERER_CLASSES:
            rclasses = [renderers.CoreJSONRenderer, renderers.BrowsableAPIRenderer]
        else:
            rclasses = [renderers.CoreJSONRenderer]
    else:
        rclasses = renderer_classes

    class SchemaView(APIView):
        _ignore_model_permissions = True
        exclude_from_schema = True
        renderer_classes = rclasses

        def get(self, request, *args, **kwargs):
            schema = generator.get_schema(request)
            if schema is None:
                raise exceptions.PermissionDenied()
            return Response(schema)

    return SchemaView.as_view()
