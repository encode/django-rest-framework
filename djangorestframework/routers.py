from django.conf.urls.defaults import patterns, url
# Note, these live in django.conf.urls since 1.4, and will no longer be
# available from django.conf.urls.defaults in 1.6.

from djangorestframework.resources import ModelResource

class DefaultResourceRouter (object):

    def __init__(self, default_resource=ModelResource):
        self.default_resource = default_resource
        self._registry = []

    @property
    def urls(self):
        """
        Return a urlpatterns object suitable for including.  I.e.:

            urlpatterns = patterns('',
                ...
                url('^api/', include(router.urls, namespace=...)),
                ...
            )
        """
        return patterns('', *self.get_urls())

    def get_urls(self):
        """
        Return a list of urls for all registered resources.
        """
        urls = []

        for model, resource in self._registry:
            urls += self.make_patterns(
                model, resource, resource.id_field_name,
                resource.collection_name, resource.instance_name
            )

        return urls

    def make_patterns(self, model, resource, id_field_name=None,
                      collection_name=None, instance_name=None):
        """
        Get the URL patterns for the given model and resource.  By default,
        this will return pair of urls -- one for the collection of resources
        representing the model, and one for individual instances of the model.
        """
        patterns = []

        if collection_name is None:
            collection_name = unicode(model._meta.verbose_name_plural)

        if instance_name is None:
            instance_name = unicode(model._meta.verbose_name)

        if id_field_name is None:
            id_field_name = u'pk'

        # The collection
        if resource.collection_view_class:
            class CollectionView (resource, resource.collection_view_class):
                pass

            collection_view = CollectionView.as_view()
            url_string = '^{0}/$'.format(collection_name)

            patterns.append(
                url(url_string, collection_view,
                    name='{0}_collection'.format(instance_name))
            )

        # The instance
        if resource.instance_view_class:
            class InstanceView (resource, resource.instance_view_class):
                pass

            instance_view = InstanceView.as_view()
            url_string = '^{0}/(?P<{1}>[^/]+)/$'.format(collection_name, id_field_name)

            patterns.append(
                url(url_string, instance_view,
                    name='{0}_instance'.format(instance_name))
             )

        return patterns

    def register(self, model, resource=None):
        """
        Register a new resource with the API.  By default a generic
        ModelResource will be used for the given model.
        """
        resource = resource or self.default_resource
        self._registry.append((model, resource))
