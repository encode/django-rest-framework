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
            self._urlpatterns = patterns('', *self.get_urlpatterns())
        return self._urlpatterns


class DefaultRouter(BaseRouter):
    route_list = [
        (r'$', {'get': 'list', 'post': 'create'}, 'list'),
        (r'(?P<pk>[^/]+)/$', {'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}, 'detail'),
    ]
    extra_routes = r'(?P<pk>[^/]+)/%s/$'
    name_format = '%s-%s'

    def get_urlpatterns(self):
        ret = []
        for prefix, viewset, base_name in self.registry:
            # Bind regular views
            if not getattr(viewset, '_is_viewset', False):
                regex = prefix
                view = viewset
                name = base_name
                ret.append(url(regex, view, name=name))
                continue

            # Bind standard CRUD routes
            for suffix, action_mapping, action_name in self.route_list:

                # Only actions which actually exist on the viewset will be bound
                bound_actions = {}
                for method, action in action_mapping.items():
                    if hasattr(viewset, action):
                        bound_actions[method] = action

                # Build the url pattern
                regex = prefix + suffix
                view = viewset.as_view(bound_actions, name_suffix=action_name)
                name = self.name_format % (base_name, action_name)
                ret.append(url(regex, view, name=name))

            # Bind any extra `@action` or `@link` routes
            for action_name in dir(viewset):
                func = getattr(viewset, action_name)
                http_method = getattr(func, 'bind_to_method', None)

                # Skip if this is not an @action or @link method
                if not http_method:
                    continue

                suffix = self.extra_routes % action_name

                # Build the url pattern
                regex = prefix + suffix
                view = viewset.as_view({http_method: action_name}, **func.kwargs)
                name = self.name_format % (base_name, action_name)
                ret.append(url(regex, view, name=name))

        # Return a list of url patterns
        return ret
