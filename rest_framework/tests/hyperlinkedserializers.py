from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import generics, status, serializers
from rest_framework.tests.models import Anchor, BasicModel, ManyToManyModel

factory = RequestFactory()


class BasicList(generics.ListCreateAPIView):
    model = BasicModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


class BasicDetail(generics.RetrieveUpdateDestroyAPIView):
    model = BasicModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


class AnchorDetail(generics.RetrieveAPIView):
    model = Anchor
    model_serializer_class = serializers.HyperlinkedModelSerializer


class ManyToManyList(generics.ListAPIView):
    model = ManyToManyModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


class ManyToManyDetail(generics.RetrieveAPIView):
    model = ManyToManyModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


urlpatterns = patterns('',
    url(r'^basic/$', BasicList.as_view(), name='basicmodel-list'),
    url(r'^basic/(?P<pk>\d+)/$', BasicDetail.as_view(), name='basicmodel-detail'),
    url(r'^anchor/(?P<pk>\d+)/$', AnchorDetail.as_view(), name='anchor-detail'),
    url(r'^manytomany/$', ManyToManyList.as_view(), name='manytomanymodel-list'),
    url(r'^manytomany/(?P<pk>\d+)/$', ManyToManyDetail.as_view(), name='manytomanymodel-detail'),
)


class TestBasicHyperlinkedView(TestCase):
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
        request = factory.get('/basic/')
        response = self.list_view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data)

    def test_get_detail_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/basic/1')
        response = self.detail_view(request, pk=1).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data[0])


class TestManyToManyHyperlinkedView(TestCase):
    urls = 'rest_framework.tests.hyperlinkedserializers'

    def setUp(self):
        """
        Create 3 BasicModel intances.
        """
        items = ['foo', 'bar', 'baz']
        anchors = []
        for item in items:
            anchor = Anchor(text=item)
            anchor.save()
            anchors.append(anchor)

        manytomany = ManyToManyModel()
        manytomany.save()
        manytomany.rel.add(*anchors)

        self.data = [{
            'url': 'http://testserver/manytomany/1/',
            'rel': [
                'http://testserver/anchor/1/',
                'http://testserver/anchor/2/',
                'http://testserver/anchor/3/',
            ]
        }]
        self.list_view = ManyToManyList.as_view()
        self.detail_view = ManyToManyDetail.as_view()

    def test_get_list_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/manytomany/')
        response = self.list_view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data)

    def test_get_detail_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/manytomany/1/')
        response = self.detail_view(request, pk=1).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data[0])
