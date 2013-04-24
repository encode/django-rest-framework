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
from django.conf.urls import url, patterns
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.urlpatterns import format_suffix_patterns


class BaseRouter(object):
    def __init__(self):
        self.registry = []

    def register(self, prefix, viewset, basename):
        self.registry.append((prefix, viewset, basename))

    def get_urls(self):
        raise NotImplemented('get_urls must be overridden')

    @property
    def urls(self):
        if not hasattr(self, '_urls'):
            self._urls = patterns('', *self.get_urls())
        return self._urls


class SimpleRouter(BaseRouter):
    routes = [
        # List route.
        (
            r'^{prefix}/$',
            {
                'get': 'list',
                'post': 'create'
            },
            '{basename}-list'
        ),
        # Detail route.
        (
            r'^{prefix}/{lookup}/$',
            {
                'get': 'retrieve',
                'put': 'update',
                'patch': 'partial_update',
                'delete': 'destroy'
            },
            '{basename}-detail'
        ),
        # Dynamically generated routes.
        # Generated using @action or @link decorators on methods of the viewset.
        (
            r'^{prefix}/{lookup}/{methodname}/$',
            {
                '{httpmethod}': '{methodname}',
            },
            '{basename}-{methodname}'
        ),
    ]

    def get_routes(self, viewset):
        """
        Augment `self.routes` with any dynamically generated routes.

        Returns a list of 4-tuples, of the form:
        `(url_format, method_map, name_format, extra_kwargs)`
        """

        # Determine any `@action` or `@link` decorated methods on the viewset
        dynamic_routes = {}
        for methodname in dir(viewset):
            attr = getattr(viewset, methodname)
            httpmethod = getattr(attr, 'bind_to_method', None)
            if httpmethod:
                dynamic_routes[httpmethod] = methodname

        ret = []
        for url_format, method_map, name_format in self.routes:
            if method_map == {'{httpmethod}': '{methodname}'}:
                # Dynamic routes
                for httpmethod, methodname in dynamic_routes.items():
                    extra_kwargs = getattr(viewset, methodname).kwargs
                    ret.append((
                        url_format.replace('{methodname}', methodname),
                        {httpmethod: methodname},
                        name_format.replace('{methodname}', methodname),
                        extra_kwargs
                    ))
            else:
                # Standard route
                extra_kwargs = {}
                ret.append((url_format, method_map, name_format, extra_kwargs))

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
        base_regex = '(?P<{lookup_field}>[^/]+)'
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

            for url_format, method_map, name_format, extra_kwargs in routes:

                # Only actions which actually exist on the viewset will be bound
                method_map = self.get_method_map(viewset, method_map)
                if not method_map:
                    continue

                # Build the url pattern
                regex = url_format.format(prefix=prefix, lookup=lookup)
                view = viewset.as_view(method_map, **extra_kwargs)
                name = name_format.format(basename=basename)
                ret.append(url(regex, view, name=name))

        return ret


class DefaultRouter(SimpleRouter):
    """
    The default router extends the SimpleRouter, but also adds in a default
    API root view, and adds format suffix patterns to the URLs.
    """
    include_root_view = True
    include_format_suffixes = True

    def get_api_root_view(self):
        """
        Return a view to use as the API root.
        """
        api_root_dict = {}
        list_name = self.routes[0][-1]
        for prefix, viewset, basename in self.registry:
            api_root_dict[prefix] = list_name.format(basename=basename)

        @api_view(('GET',))
        def api_root(request, format=None):
            ret = {}
            for key, url_name in api_root_dict.items():
                ret[key] = reverse(url_name, request=request, format=format)
            return Response(ret)

        return api_root

    def get_urls(self):
        """
        Generate the list of URL patterns, including a default root view
        for the API, and appending `.json` style format suffixes.
        """
        urls = []

        if self.include_root_view:
            root_url = url(r'^$', self.get_api_root_view(), name='api-root')
            urls.append(root_url)

        default_urls = super(DefaultRouter, self).get_urls()
        urls.extend(default_urls)

        if self.include_format_suffixes:
            urls = format_suffix_patterns(urls)

        return urls
