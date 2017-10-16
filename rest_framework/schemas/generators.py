"""
generators.py   # Top-down schema generation

See schemas.__init__.py for package overview.
"""
import warnings
from collections import Counter, OrderedDict
from importlib import import_module

from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import six

from rest_framework import exceptions
from rest_framework.compat import (
    RegexURLPattern, RegexURLResolver, coreapi, coreschema, get_regex_pattern
)
from rest_framework.request import clone_request
from rest_framework.settings import api_settings
from rest_framework.utils.model_meta import _get_pk

from .utils import is_list_view


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
    # Avoid import cycle on APIView
    from rest_framework.views import APIView
    cls = getattr(callback, 'cls', None)
    return (cls is not None) and issubclass(cls, APIView)


INSERT_INTO_COLLISION_FMT = """
Schema Naming Collision.

coreapi.Link for URL path {value_url} cannot be inserted into schema.
Position conflicts with coreapi.Link for URL path {target_url}.

Attemped to insert link with keys: {keys}.

Adjust URLs to avoid naming collision or override `SchemaGenerator.get_keys()`
to customise schema structure.
"""


class LinkNode(OrderedDict):
    def __init__(self):
        self.links = []
        self.methods_counter = Counter()
        super(LinkNode, self).__init__()

    def get_available_key(self, preferred_key):
        if preferred_key not in self:
            return preferred_key

        while True:
            current_val = self.methods_counter[preferred_key]
            self.methods_counter[preferred_key] += 1

            key = '{}_{}'.format(preferred_key, current_val)
            if key not in self:
                return key


def insert_into(target, keys, value):
    """
    Nested dictionary insertion.

    >>> example = {}
    >>> insert_into(example, ['a', 'b', 'c'], 123)
    >>> example
    LinkNode({'a': LinkNode({'b': LinkNode({'c': LinkNode(links=[123])}}})))
    """
    for key in keys[:-1]:
        if key not in target:
            target[key] = LinkNode()
        target = target[key]

    try:
        target.links.append((keys[-1], value))
    except TypeError:
        msg = INSERT_INTO_COLLISION_FMT.format(
            value_url=value.url,
            target_url=target.url,
            keys=keys
        )
        raise ValueError(msg)


def distribute_links(obj):
    for key, value in obj.items():
        distribute_links(value)

    for preferred_key, link in obj.links:
        key = obj.get_available_key(preferred_key)
        obj[key] = link


def is_custom_action(action):
    return action not in set([
        'retrieve', 'list', 'create', 'update', 'partial_update', 'destroy'
    ])


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


class EndpointEnumerator(object):
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
            path_regex = prefix + get_regex_pattern(pattern)
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

        if hasattr(callback.cls, 'exclude_from_schema'):
            fmt = ("The `{}.exclude_from_schema` attribute is pending deprecation. "
                   "Set `schema = None` instead.")
            msg = fmt.format(callback.cls.__name__)
            warnings.warn(msg, PendingDeprecationWarning)
            if getattr(callback.cls, 'exclude_from_schema', False):
                return False

        if callback.cls.schema is None:
            return False

        if path.endswith('.{format}') or path.endswith('.{format}/'):
            return False  # Ignore .json style URLs.

        return True

    def get_allowed_methods(self, callback):
        """
        Return a list of the valid HTTP methods for this endpoint.
        """
        if hasattr(callback, 'actions'):
            actions = set(callback.actions.keys())
            http_method_names = set(callback.cls.http_method_names)
            return [method.upper() for method in actions & http_method_names]

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
    endpoint_inspector_cls = EndpointEnumerator

    # Map the method names we use for viewset actions onto external schema names.
    # These give us names that are more suitable for the external representation.
    # Set by 'SCHEMA_COERCE_METHOD_NAMES'.
    coerce_method_names = None

    # 'pk' isn't great as an externally exposed name for an identifier,
    # so by default we prefer to use the actual model field name for schemas.
    # Set by 'SCHEMA_COERCE_PATH_PK'.
    coerce_path_pk = None

    def __init__(self, title=None, url=None, description=None, patterns=None, urlconf=None):
        assert coreapi, '`coreapi` must be installed for schema support.'
        assert coreschema, '`coreschema` must be installed for schema support.'

        if url and not url.endswith('/'):
            url += '/'

        self.coerce_method_names = api_settings.SCHEMA_COERCE_METHOD_NAMES
        self.coerce_path_pk = api_settings.SCHEMA_COERCE_PATH_PK

        self.patterns = patterns
        self.urlconf = urlconf
        self.title = title
        self.description = description
        self.url = url
        self.endpoints = None

    def get_schema(self, request=None, public=False):
        """
        Generate a `coreapi.Document` representing the API schema.
        """
        if self.endpoints is None:
            inspector = self.endpoint_inspector_cls(self.patterns, self.urlconf)
            self.endpoints = inspector.get_api_endpoints()

        links = self.get_links(None if public else request)
        if not links:
            return None

        url = self.url
        if not url and request is not None:
            url = request.build_absolute_uri()

        distribute_links(links)
        return coreapi.Document(
            title=self.title, description=self.description,
            url=url, content=links
        )

    def get_links(self, request=None):
        """
        Return a dictionary containing all the links that should be
        included in the API schema.
        """
        links = LinkNode()

        # Generate (path, method, view) given (path, method, callback).
        paths = []
        view_endpoints = []
        for path, method, callback in self.endpoints:
            view = self.create_view(callback, method, request)
            path = self.coerce_path(path, method, view)
            paths.append(path)
            view_endpoints.append((path, method, view))

        # Only generate the path prefix for paths that will be included
        if not paths:
            return None
        prefix = self.determine_path_prefix(paths)

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            link = view.schema.get_link(path, method, base_url=self.url)
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
        except (exceptions.APIException, Http404, PermissionDenied):
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
