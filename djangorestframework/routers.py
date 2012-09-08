from django.conf.urls import patterns, url
from djangorestframework.resources import ModelResource

class DefaultResourceRouter (object):

    def __init__(self, resource=ModelResource):
        self.resource = resource
        self._registry = []

    @property
    def urls(self):
        return self.get_urls()

    def get_urls(self):
        urls = []
        for model, resource in self._registry:
            urls += self.make_patterns(model, resource,
                                       id_field_name=resource.id_field_name,
                                       collection_name=resource.collection_name,
                                       instance_name=resource.instance_name)
        return patterns('', *urls)

    def make_patterns(self, model, resource, id_field_name=None,
                      collection_name=None, instance_name=None):
        patterns = []

        # The collection_name is the path at the root of the resource.  For
        # example, say we have a Dog model, and a dog with id=1:
        #
        #     http://api.example.com/dogs/1/
        #
        # The collection name is 'dogs'.  This will default to the plural name
        # for the model.
        #
        if collection_name is None:
            collection_name = unicode(model._meta.verbose_name_plural)

        # The instance_name is the name of one model instance, and is used as a
        # prefix for internal URL names.  For example, for out Dog model with
        # instance_name 'dog', may have the following urls:
        #
        #     url('dogs/', collection_view, name='dog_collection'),
        #     url('dogs/(P<pk>[^/])/)', instance_view, name='dog_instance'),
        #
        if instance_name is None:
            instance_name = unicode(model._meta.verbose_name)

        # The id_field_name is the name of the field that will identify a
        # resource in the collection.  For example, if we wanted our dogs
        # identified by a 'slug' field, we would have:
        #
        #     url('dogs/(P<slug>[^/])/)', instance_view, name='dog_instance'),
        #
        # and:
        #
        #     http://api.example.com/dogs/fido/
        #
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
        resource = resource or self.resource
        self._registry.append((model, resource))
