from django.conf.urls.defaults import patterns, url, include
from collections import defaultdict

class ApiEntry(object):
    """
    Hold a list of urlpatterns for a given Resource in the API
    """
    
    def __init__(self, resource, view, name, namespace=None):
        self.resource, self.view, self.name = resource, view, name
        self.namespace = namespace is not None and namespace or ''
        
    def get_urls(self):
        """
        Create the URLs corresponding to this view.
        """
        from djangorestframework.mixins import ListModelMixin, InstanceMixin
        if self.namespace == '':
            namespaced_name = self.name
        else:
            namespaced_name = '%s/%s' % (self.namespace, self.name)

        if issubclass(self.view, ListModelMixin):
            urlpatterns = patterns('',
                url(r'^%s/$' % (namespaced_name),
                    self.view.as_view(resource=self.resource),
                    name=self.name,
                    )
            )
        elif issubclass(self.view, InstanceMixin):
            # This regex pattern is intentionally designed to match primary 
            # keys which are integers, letters or both.
            # An improvement would be to infer the right primary key regex from 
            # the model in the resource, to prevent matching non-numeric
            # primary keys in the URL when the model can only have numeric
            # primary keys
            urlpatterns = patterns('',
                url(r'^%s/(?P<pk>[0-9a-zA-Z]+)/$' % (namespaced_name),
                    self.view.as_view(resource=self.resource),
                    name=self.name + '_change',
                    )
            )
        return urlpatterns
    
    @property
    def urls(self):
        return self.get_urls(), 'api', self.namespace

class Api(object):
    app_name = 'api'
    namespace = 'api'
    api_entry_class = ApiEntry

    def __init__(self, api_entry_class=None):
        self._registry = defaultdict(lambda: defaultdict(list))
        if api_entry_class is not None:
            self.api_entry_class = api_entry_class

    def register(self, view, resource, namespace=None, name=None):
        """
        Register a resource and a view into the API, optionally giving an 
        override for the resource's name and a namespace for the URLs.
        """
        if name is None:
            if hasattr(resource, 'model'):
                # Use the model's name as the resource_name
                name = resource.model.__name__.lower()
            else:
                # Use the Resource's name as the resource_name
                name = resource.__name__.lower()
        
        resource.api_name = name
            
        api_entry = self.get_api_entry(
            resource=resource, view=view, name=name, namespace=namespace
        )
        self._registry[namespace][name].append(api_entry)

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace
    
    def get_api_entry(self, resource, view, name, namespace):
        return self.api_entry_class(resource, view, name, namespace)
        
    def get_urls(self):
        """
        Return all of the urls for this API
        """

        # Site-wide views.
        urlpatterns = patterns('',)

        # Add in each resource's views.
        for namespace in self._registry.keys():
            for resource_name in self._registry[namespace].keys():
                for api_entry in self._registry[namespace][resource_name]:
                    urlpatterns += patterns('',
                        url(r'^', include(api_entry.urls))
                    )
            
        return urlpatterns
