from djangorestframework.mixins import ListModelMixin, InstanceMixin
from django.conf.urls.defaults import patterns, url

class DjangoRestFrameworkSite(object):
    app_name = 'api'
    name = 'api'

    def __init__(self, *args, **kwargs):
        self._registry = {}
        super(DjangoRestFrameworkSite, self).__init__(*args, **kwargs)

    def register(self, view, resource, prefix=None, resource_name=None):
        if resource_name is None:
            if hasattr(resource, 'model'):
                resource_name = resource.model.__name__.lower()
            else:
                resource_name = resource.__name__.lower()
        
        if prefix not in self._registry:
            self._registry[prefix] = {}
            
        if resource_name not in self._registry[prefix]:
            self._registry[prefix][resource_name] = []
            
        self._registry[prefix][resource_name].append((resource, view))


#    def unregister(self, prefix=None, resource_name=None, resource=None):
#        """
#        Unregisters a resource.
#        """
#        if resource_name is None and resource is not None and \
#        hasattr(resource, 'model'):
#            resource_name = resource.model.__name__.lower()
#            
#        if resource_name is None:
#            # do nothing
#            return
#            
#        prefix_registry = self._registry.get(prefix, {})
#        if resource_name in prefix_registry:
#            del prefix_registry[resource_name]

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.name
    
    def get_urls(self):

        # Site-wide views.
        urlpatterns = patterns('',


        )

        # Add in each resource's views.
        for prefix in self._registry.keys():
            for resource_name in self._registry[prefix].keys():
                for resource, view in self._registry[prefix][resource_name]:
                    urlpatterns += self.__get_urlpatterns(
                        prefix, resource_name, resource, view
                    )

        return urlpatterns
    
    def __get_urlpatterns(self, prefix, resource_name, resource, view):
        """
        Calculates the URL pattern for a given resource and view
        """
        if prefix is None:
            prefix = ''
        else:
            prefix += '/'
        if issubclass(view, ListModelMixin):
            urlpatterns = patterns('',
                url(r'^%s%s/$' % (prefix,resource_name),
                    view.as_view(resource=resource),
                    name=resource_name
                    )
            )
        elif issubclass(view, InstanceMixin):
            urlpatterns = patterns('',
                url(r'^%s%s/(?P<pk>[0-9]+)/$' % (prefix,resource_name),
                    view.as_view(resource=resource),
                    name=resource_name + '_change'
                    )
            )
            
        return urlpatterns
