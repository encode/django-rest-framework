
from django.conf.urls.defaults import patterns, url, include
from django.views.decorators.csrf import csrf_exempt

class ApiEntry(object):
    def __init__(self, resource, view, prefix, resource_name):
        self.resource, self.view = resource, view
        self.prefix, self.resource_name = prefix, resource_name
        if self.prefix is None:
            self.prefix = ''
        
    def get_urls(self):
        from djangorestframework.mixins import ListModelMixin, InstanceMixin
        from django.conf.urls.defaults import patterns, url

        if self.prefix == '':
            url_prefix = ''
        else:
            url_prefix = self.prefix + '/'

        if issubclass(self.view, ListModelMixin):
            urlpatterns = patterns('',
                url(r'^%s%s/$' % (url_prefix, self.resource_name),
                    self.view.as_view(resource=self.resource),
                    name=self.resource_name,
                    )
            )
        elif issubclass(self.view, InstanceMixin):
            urlpatterns = patterns('',
                url(r'^%s%s/(?P<pk>[0-9a-zA-Z]+)/$' % (url_prefix, self.resource_name),
                    self.view.as_view(resource=self.resource),
                    name=self.resource_name + '_change',
                    )
            )
        return urlpatterns
    

    def urls(self):
        return self.get_urls(), 'api', self.prefix
    urls = property(urls)

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
        
        resource.resource_name = resource_name
        
        if prefix not in self._registry:
            self._registry[prefix] = {}
            
        if resource_name not in self._registry[prefix]:
            self._registry[prefix][resource_name] = []
            
        api_entry = ApiEntry(resource, view, prefix, resource_name)
        self._registry[prefix][resource_name].append(api_entry)


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
                for api_entry in self._registry[prefix][resource_name]:
                    urlpatterns += patterns('',
                        url(r'^', include(api_entry.urls))
                    )
 
            
        return urlpatterns

