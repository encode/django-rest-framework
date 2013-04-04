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

    def get_urlpatterns(self):
        ret = []
        for prefix, viewset, base_name in self.registry:
            for suffix, action_mapping, name_format in self.route_list:

                # Only actions which actually exist on the viewset will be bound
                bound_actions = {}
                for method, action in action_mapping.items():
                    if hasattr(viewset, action):
                        bound_actions[method] = action

                regex = prefix + suffix
                view = viewset.as_view(bound_actions)
                name = name_format % base_name
                ret.append(url(regex, view, name=name))
        return ret
