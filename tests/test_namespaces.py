from django.conf.urls import include, url
from django.db import models

from rest_framework import serializers, status, viewsets
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIRequestFactory, APITestCase

from .urls import urlpatterns

factory = APIRequestFactory()


# no namesapce: Model, serializer and viewset


class NoNamespaceModel(models.Model):
    pass


class NoNamespaceModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NoNamespaceModel


class NoNamespaceModelViewSet(viewsets.ModelViewSet):
    queryset = NoNamespaceModel.objects.all()
    serializer_class = NoNamespaceModelSerializer


no_namespace_router = DefaultRouter()
no_namespace_router.register('no_ns_model', NoNamespaceModelViewSet)


# namespace1: Model, serializer and viewset


class Namespace1Model(models.Model):
    # Reference to NoNamespaceModel
    fk_no_ns_model = models.ForeignKey(NoNamespaceModel)


class Namespace1ModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Namespace1Model


class Namespace1ModelViewSet(viewsets.ModelViewSet):
    queryset = Namespace1Model.objects.all()
    serializer_class = Namespace1ModelSerializer


namespace1_router = DefaultRouter()
namespace1_router.register('ns_1_model', Namespace1ModelViewSet)


# namespace2: Models, serializers and viewsets


class Namespace2Model1(models.Model):
    # Reference to Namespace1Model
    fk_ns_1_model = models.ForeignKey(Namespace1Model)


class Namespace2Model2(models.Model):
    # Reference to Namespace2Model1
    fk_ns_2_model_1 = models.ForeignKey(Namespace2Model1)


class Namespace2Model1Serializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Namespace2Model1


class Namespace2Model2Serializer(serializers.HyperlinkedModelSerializer):
    fk_ns_2_model_1 = Namespace2Model1Serializer(read_only=True)

    class Meta:
        model = Namespace2Model2


class Namespace2Model1ViewSet(viewsets.ModelViewSet):
    queryset = Namespace2Model1.objects.all()
    serializer_class = Namespace2Model1Serializer


class Namespace2Model2ViewSet(viewsets.ModelViewSet):
    queryset = Namespace2Model2.objects.all()
    serializer_class = Namespace2Model2Serializer


namespace2_router = DefaultRouter()
namespace2_router.register('ns_2_model_1', Namespace2Model1ViewSet)
namespace2_router.register('ns_2_model_2', Namespace2Model2ViewSet)


urlpatterns += [
    url(r'^nonamespace/', include(no_namespace_router.urls)),
    url(r'^namespace1/', include(namespace1_router.urls, namespace='namespace1')),
    url(r'^namespace2/', include(namespace2_router.urls, namespace='namespace2')),
]


class NamespaceTestCase(APITestCase):

    def setUp(self):
        self.request = factory.request()
        self.no_ns_item = NoNamespaceModel.objects.create()
        self.ns_1_item = Namespace1Model.objects.create(fk_no_ns_model=self.no_ns_item)
        self.ns_2_model_1_item = Namespace2Model1.objects.create(fk_ns_1_model=self.ns_1_item)
        self.ns_2_model_2_item = Namespace2Model2.objects.create(fk_ns_2_model_1=self.ns_2_model_1_item)
        self.url_no_ns_item = '/nonamespace/no_ns_model/{pk}/'.format(pk=self.no_ns_item.pk)
        self.url_ns_1_item = '/namespace1/ns_1_model/{pk}/'.format(pk=self.ns_1_item.pk)
        self.url_ns_2_model_1_item = '/namespace2/ns_2_model_1/{pk}/'.format(pk=self.ns_2_model_1_item.pk)
        self.url_ns_2_model_2_item = '/namespace2/ns_2_model_2/{pk}/'.format(pk=self.ns_2_model_2_item.pk)

    def test_reverse_with_namespace(self):
        # Namespace 1
        reverse_ns_1_item = reverse('namespace1:namespace1model-detail', args=[self.ns_1_item.pk])
        self.assertEquals(reverse_ns_1_item, self.url_ns_1_item)

        # Namespace 2 - Model 1
        reverse_ns_2_model_1_item = reverse('namespace2:namespace2model1-detail', args=[self.ns_2_model_1_item.pk])
        self.assertEquals(reverse_ns_2_model_1_item, self.url_ns_2_model_1_item)

        # Namespace 2 - Model 2
        reverse_ns_2_model_2_item = reverse('namespace2:namespace2model2-detail', args=[self.ns_2_model_2_item.pk])
        self.assertEquals(reverse_ns_2_model_2_item, self.url_ns_2_model_2_item)

    def test_hyperlinked_identity_field_with_no_namespace(self):
        response = self.client.get(self.url_ns_1_item)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data.get('url', None), self.request.build_absolute_uri(self.url_ns_1_item))

        # Test the hyperlink of the NoNamespaceModel FK
        fk_url = response.data.get('fk_no_ns_model', None)
        self.assertEquals(fk_url, self.request.build_absolute_uri(self.url_no_ns_item))

    def test_hyperlinked_identity_field_with_different_namespace(self):
        response = self.client.get(self.url_ns_2_model_1_item)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data.get('url', None), self.request.build_absolute_uri(self.url_ns_2_model_1_item))
        # Test the hyperlink of the NameSpace1Model FK
        self.assertEquals(response.data.get('fk_ns_1_model', None), self.request.build_absolute_uri(self.url_ns_1_item))

    def test_hyperlinked_identity_field_with_same_namespace(self):
        response = self.client.get(self.url_ns_2_model_2_item)
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data.get('url', None), self.request.build_absolute_uri(self.url_ns_2_model_2_item))
        response_item = response.data.get('fk_ns_2_model_1', {})
        # Test the hyperlink of the Namespace2Model1 FK
        self.assertEquals(response_item.get('url', None), self.request.build_absolute_uri(self.url_ns_2_model_1_item))
        # Test the hyperlink of the NameSpace1Model FK
        self.assertEquals(response_item.get('fk_ns_1_model', None), self.request.build_absolute_uri(self.url_ns_1_item))
