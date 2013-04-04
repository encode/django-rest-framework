from django.conf.urls import url, patterns


class BaseRouter(object):
    def __init__(self):
        self.registry = []

    def register(self, prefix, viewset, base_name):
        self.registry.append((prefix, viewset, base_name))

    def get_urlpatterns(self):
        raise NotImplemented('get_urlpatterns must be overridden')

    @property
    def urlpatterns(self):
        if not hasattr(self, '_urlpatterns'):
            print self.get_urlpatterns()
            self._urlpatterns = patterns('', *self.get_urlpatterns())
        return self._urlpatterns


class DefaultRouter(BaseRouter):
    route_list = [
        (r'$', {'get': 'list', 'post': 'create'}, '%s-list'),
        (r'(?P<pk>[^/]+)/$', {'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}, '%s-detail'),
    ]
    extra_routes = (r'(?P<pk>[^/]+)/%s/$', '%s-%s')

    def get_urlpatterns(self):
        ret = []
        for prefix, viewset, base_name in self.registry:
            # Bind standard routes
            for suffix, action_mapping, name_format in self.route_list:

                # Only actions which actually exist on the viewset will be bound
                bound_actions = {}
                for method, action in action_mapping.items():
                    if hasattr(viewset, action):
                        bound_actions[method] = action

                # Build the url pattern
                regex = prefix + suffix
                view = viewset.as_view(bound_actions)
                name = name_format % base_name
                ret.append(url(regex, view, name=name))

            # Bind any extra @action or @link routes
            for attr in dir(viewset):
                func = getattr(viewset, attr)
                http_method = getattr(func, 'bind_to_method', None)
                if not http_method:
                    continue

                regex_format, name_format = self.extra_routes

                # Build the url pattern
                regex = regex_format % attr
                view = viewset.as_view({http_method: attr}, **func.kwargs)
                name = name_format % (base_name, attr)
                ret.append(url(regex, view, name=name))

        # Return a list of url patterns
        return ret
