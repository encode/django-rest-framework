from django.conf.urls import patterns, url
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import generics, status, serializers
from rest_framework.tests.models import BasicModel

factory = RequestFactory()


class BasicList(generics.ListCreateAPIView):
    model = BasicModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


class BasicDetail(generics.RetrieveUpdateDestroyAPIView):
    model = BasicModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


urlpatterns = patterns('',
    url(r'^basic/$', BasicList.as_view(), name='basicmodel-list'),
    url(r'^basic/(?P<pk>\d+)/$', BasicDetail.as_view(), name='basicmodel-detail'),
)


class TestHyperlinkedView(TestCase):
    urls = 'rest_framework.tests.hyperlinkedserializers'

    def setUp(self):
        """
        Create 3 BasicModel intances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'url': 'http://testserver/basic/%d/' % obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]
        self.list_view = BasicList.as_view()
        self.detail_view = BasicDetail.as_view()

    def test_get_list_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/')
        response = self.list_view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data)

    def test_get_detail_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/1')
        response = self.detail_view(request, pk=1).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data[0])
