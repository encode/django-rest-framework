from djangorestframework.serializers import ModelSerializer
from djangorestframework.generics import RootAPIView, InstanceAPIView

class ModelResource (object):
    serializer_class = ModelSerializer
    collection_view_class = RootAPIView
    instance_view_class = InstanceAPIView

    collection_name = None
    instance_name = None
    id_field_name = 'pk'
