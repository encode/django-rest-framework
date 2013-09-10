"""
Routers provide a convenient and consistent way of automatically
determining the URL conf for your API.

They are used by simply instantiating a Router class, and then registering
all the required ViewSets with that router.

For example, you might have a `urls.py` that looks something like this:

    router = routers.DefaultRouter()
    router.register('users', UserViewSet, 'user')
    router.register('accounts', AccountViewSet, 'account')

    urlpatterns = router.urls
"""
from __future__ import unicode_literals

import itertools
from collections import namedtuple
from django.core.exceptions import ImproperlyConfigured
from rest_framework import views
from rest_framework.compat import patterns, url
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns


Route = namedtuple('Route', ['url', 'mapping', 'name', 'initkwargs'])


def replace_methodname(format_string, methodname):
    """
    Partially format a format_string, swapping out any
    '{methodname}' or '{methodnamehyphen}' components.
    """
    methodnamehyphen = methodname.replace('_', '-')
    ret = format_string
    ret = ret.replace('{methodname}', methodname)
    ret = ret.replace('{methodnamehyphen}', methodnamehyphen)
    return ret


def flatten(list_of_lists):
    """
    Takes an iterable of iterables, returns a single iterable containing all items
    """
    return itertools.chain(*list_of_lists)


class BaseRouter(object):
    def __init__(self):
        self.registry = []

    def register(self, prefix, viewset, base_name=None):
        if base_name is None:
            base_name = self.get_default_base_name(viewset)
        self.registry.append((prefix, viewset, base_name))

    def get_default_base_name(self, viewset):
        """
        If `base_name` is not specified, attempt to automatically determine
        it from the viewset.
        """
        raise NotImplemented('get_default_base_name must be overridden')

    def get_urls(self):
        """
        Return a list of URL patterns, given the registered viewsets.
        """
        raise NotImplemented('get_urls must be overridden')

    @property
    def urls(self):
        if not hasattr(self, '_urls'):
            self._urls = patterns('', *self.get_urls())
        return self._urls


class SimpleRouter(BaseRouter):
    routes = [
        # List route.
        Route(
            url=r'^{prefix}{trailing_slash}$',
            mapping={
                'get': 'list',
                'post': 'create'
            },
            name='{basename}-list',
            initkwargs={'suffix': 'List'}
        ),
        # Detail route.
        Route(
            url=r'^{prefix}/{lookup}{trailing_slash}$',
            mapping={
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            name='{basename}-detail',
            initkwargs={'suffix': 'Instance'}
        ),
        # Dynamically generated routes.
        # Generated using @action or @link decorators on methods of the viewset.
        Route(
            url=r'^{prefix}/{lookup}/{methodname}{trailing_slash}$',
            mapping={
                '{httpmethod}': '{methodname}',
            },
            name='{basename}-{methodnamehyphen}',
            initkwargs={}
        ),
    ]

    def __init__(self, trailing_slash=True):
        self.trailing_slash = trailing_slash and '/' or ''
        super(SimpleRouter, self).__init__()

    def get_default_base_name(self, viewset):
        """
        If `base_name` is not specified, attempt to automatically determine
        it from the viewset.
        """
        model_cls = getattr(viewset, 'model', None)
        queryset = getattr(viewset, 'queryset', None)
        if model_cls is None and queryset is not None:
            model_cls = queryset.model

        assert model_cls, '`base_name` argument not specified, and could ' \
            'not automatically determine the name from the viewset, as ' \
            'it does not have a `.model` or `.queryset` attribute.'

        return model_cls._meta.object_name.lower()

    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.

        Returns a list of the Route namedtuple.
        """

        known_actions = flatten([route.mapping.values() for route in self.routes])

        # Determine any `@action` or `@link` decorated methods on the viewset
        dynamic_routes = []
        for methodname in dir(viewset):
            attr = getattr(viewset, methodname)
            httpmethods = getattr(attr, 'bind_to_methods', None)
            if httpmethods:
                if methodname in known_actions:
                    raise ImproperlyConfigured('Cannot use @action or @link decorator on '
                                               'method "%s" as it is an existing route' % methodname)
                httpmethods = [method.lower() for method in httpmethods]
                dynamic_routes.append((httpmethods, methodname))

        ret = []
        for route in self.routes:
            if route.mapping == {'{httpmethod}': '{methodname}'}:
                # Dynamic routes (@link or @action decorator)
                for httpmethods, methodname in dynamic_routes:
                    initkwargs = route.initkwargs.copy()
                    initkwargs.update(getattr(viewset, methodname).kwargs)
                    ret.append(Route(
                        url=replace_methodname(route.url, methodname),
                        mapping=dict((httpmethod, methodname) for httpmethod in httpmethods),
                        name=replace_methodname(route.name, methodname),
                        initkwargs=initkwargs,
                    ))
            else:
                # Standard route
                ret.append(route)

        return ret

    def get_method_map(self, viewset, method_map):
        """
        Given a viewset, and a mapping of http methods to actions,
        return a new mapping which only includes any mappings that
        are actually implemented by the viewset.
        """
        bound_methods = {}
        for method, action in method_map.items():
            if hasattr(viewset, action):
                bound_methods[method] = action
        return bound_methods

    def get_lookup_regex(self, viewset):
        """
        Given a viewset, return the portion of URL regex that is used
        to match against a single instance.
        """
        if self.trailing_slash:
            base_regex = '(?P<{lookup_field}>[^/]+)'
        else:
            # Don't consume `.json` style suffixes
            base_regex = '(?P<{lookup_field}>[^/.]+)'
        lookup_field = getattr(viewset, 'lookup_field', 'pk')
        return base_regex.format(lookup_field=lookup_field)

    def get_urls(self):
        """
        Use the registered viewsets to generate a list of URL patterns.
        """
        ret = []

        for prefix, viewset, basename in self.registry:
            lookup = self.get_lookup_regex(viewset)
            routes = self.get_routes(viewset)

            for route in routes:

                # Only actions which actually exist on the viewset will be bound
                mapping = self.get_method_map(viewset, route.mapping)
                if not mapping:
                    continue

                # Build the url pattern
                regex = route.url.format(
                    prefix=prefix,
                    lookup=lookup,
                    trailing_slash=self.trailing_slash
                )
                view = viewset.as_view(mapping, **route.initkwargs)
                name = route.name.format(basename=basename)
                ret.append(url(regex, view, name=name))

        return ret


class DefaultRouter(SimpleRouter):
    """
    The default router extends the SimpleRouter, but also adds in a default
    API root view, and adds format suffix patterns to the URLs.
    """
    include_root_view = True
    include_format_suffixes = True
    root_view_name = 'api-root'

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = {}
        list_name = self.routes[0].name
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        class APIRoot(views.APIView):
            _ignore_model_permissions = True

            def get(self, request, format=None):
                ret = {}
                for key, url_name in api_root_dict.items():
                    ret[key] = reverse(url_name, request=request, format=format)
                return Response(ret)

        return APIRoot.as_view()

    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = []

        if self.include_root_view:
            root_url = url(r'^$', self.get_api_root_view(), name=self.root_view_name)
            urls.append(root_url)

        default_urls = super(DefaultRouter, self).get_urls()
        urls.extend(default_urls)

        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls)

        return urls
