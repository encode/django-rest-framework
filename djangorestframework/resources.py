from djangorestframework.serializers import ModelSerializer
from djangorestframework.generics import RootAPIView, InstanceAPIView

class ModelResource (object):
    serializer_class = ModelSerializer
    collection_view_class = RootAPIView
    instance_view_class = InstanceAPIView

    # The collection_name is the path at the root of the resource.  For
    # example, say we have a Dog model, and a dog with id=1:
    #
    #     http://api.example.com/dogs/1/
    #
    # The collection name is 'dogs'.  This will default to the plural name
    # for the model.
    #
    collection_name = None

    # The instance_name is the name of one model instance, and is used as a
    # prefix for internal URL names.  For example, for out Dog model with
    # instance_name 'dog', may have the following urls:
    #
    #     url('dogs/', collection_view, name='dog_collection'),
    #     url('dogs/(P<pk>[^/])/)', instance_view, name='dog_instance'),
    #
    instance_name = None

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
    # The default value is 'pk'.
    #
    id_field_name = 'pk'
