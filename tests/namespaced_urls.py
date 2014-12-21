from django.conf.urls import url, include
from django.db import models

from rest_framework import serializers, viewsets, routers


class NamespacedRouterTestModel(models.Model):
    uuid = models.CharField(max_length=20)
    text = models.CharField(max_length=200)


class NoteSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='api-namespace:routertestmodel-detail', lookup_field='uuid')

    class Meta:
        model = NamespacedRouterTestModel
        fields = ('url', 'uuid', 'text')


class NoteViewSet(viewsets.ModelViewSet):
    queryset = NamespacedRouterTestModel.objects.all()
    serializer_class = NoteSerializer
    lookup_field = 'uuid'

router = routers.DefaultRouter(namespace='api-namespace')

router.register(r'note', NoteViewSet)


urlpatterns = [
    url('^namespaced-api/', include(router.urls, namespace='api-namespace')),
]
