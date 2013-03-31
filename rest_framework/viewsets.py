# Not properly implemented yet, just the basic idea


class BaseRouter(object):
    def __init__(self):
        self.resources = []

    def register(self, name, resource):
        self.resources.append((name, resource))

    @property
    def urlpatterns(self):
        ret = []

        for name, resource in self.resources:
            list_actions = {
                'get': getattr(resource, 'list', None),
                'post': getattr(resource, 'create', None)
            }
            detail_actions = {
                'get': getattr(resource, 'retrieve', None),
                'put': getattr(resource, 'update', None),
                'delete': getattr(resource, 'destroy', None)
            }
            list_regex = r'^%s/$' % name
            detail_regex = r'^%s/(?P<pk>[0-9]+)/$' % name
            list_name = '%s-list'
            detail_name = '%s-detail'

            ret += url(list_regex, resource.as_view(list_actions), list_name)
            ret += url(detail_regex, resource.as_view(detail_actions), detail_name)

        return ret
