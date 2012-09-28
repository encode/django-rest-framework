from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import generics, status
from rest_framework.tests.models import BasicModel


factory = RequestFactory()


class RootView(generics.RootAPIView):
    model = BasicModel


class TestListView(TestCase):
    def setUp(self):
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]

    def test_get_root_view(self):
        view = RootView.as_view()
        request = factory.get('/')
        response = view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data, self.data)
