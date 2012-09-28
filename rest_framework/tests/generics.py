from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import simplejson as json
from rest_framework import generics, status
from rest_framework.tests.models import BasicModel


factory = RequestFactory()


class RootView(generics.RootAPIView):
    model = BasicModel


class InstanceView(generics.InstanceAPIView):
    model = BasicModel


class TestRootView(TestCase):
    def setUp(self):
        """
        Create 3 BasicModel intances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]

    def test_get_root_view(self):
        """
        GET requests to RootAPIView should return list of objects.
        """
        view = RootView.as_view()
        request = factory.get('/')
        response = view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data)

    def test_post_root_view(self):
        """
        POST requests to RootAPIView should create a new object.
        """
        view = RootView.as_view()
        content = {'text': 'foobar'}
        request = factory.post('/', json.dumps(content), content_type='application/json')
        response = view(request).render()
        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(response.data, {'id': 4, 'text': u'foobar'})
        created = self.objects.get(id=4)
        self.assertEquals(created.text, 'foobar')


class TestInstanceView(TestCase):
    def setUp(self):
        """
        Create 3 BasicModel intances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]

    def test_get_instance_view(self):
        """
        GET requests to InstanceAPIView should return a single object.
        """
        view = InstanceView.as_view()
        request = factory.get('/1')
        response = view(request, pk=1).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data[0])

    def test_put_instance_view(self):
        """
        PUT requests to InstanceAPIView should update an object.
        """
        view = InstanceView.as_view()
        content = {'text': 'foobar'}
        request = factory.put('/1', json.dumps(content), content_type='application/json')
        response = view(request, pk=1).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, {'id': 1, 'text': 'foobar'})
        updated = self.objects.get(id=1)
        self.assertEquals(updated.text, 'foobar')

    def test_delete_instance_view(self):
        """
        DELETE requests to InstanceAPIView should delete an object.
        """
        view = InstanceView.as_view()
        request = factory.delete('/1')
        response = view(request, pk=1).render()
        self.assertEquals(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEquals(response.content, '')
        ids = [obj.id for obj in self.objects.all()]
        self.assertEquals(ids, [2, 3])
