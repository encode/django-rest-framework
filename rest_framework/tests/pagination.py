from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import generics, status
from rest_framework.tests.models import BasicModel

factory = RequestFactory()


class RootView(generics.RootAPIView):
    """
    Example description for OPTIONS.
    """
    model = BasicModel
    paginate_by = 10


class TestPaginatedView(TestCase):
    def setUp(self):
        """
        Create 26 BasicModel intances.
        """
        for char in 'abcdefghijklmnopqrstuvwxyz':
            BasicModel(text=char * 3).save()
        self.objects = BasicModel.objects
        self.data = [
            {'id': obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]
        self.view = RootView.as_view()

    def test_get_paginated_root_view(self):
        """
        GET requests to paginated RootAPIView should return paginated results.
        """
        request = factory.get('/')
        response = self.view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 26)
        self.assertEquals(response.data['results'], self.data[:10])
        self.assertNotEquals(response.data['next'], None)
        self.assertEquals(response.data['previous'], None)

        request = factory.get(response.data['next'])
        response = self.view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 26)
        self.assertEquals(response.data['results'], self.data[10:20])
        self.assertNotEquals(response.data['next'], None)
        self.assertNotEquals(response.data['previous'], None)

        request = factory.get(response.data['next'])
        response = self.view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 26)
        self.assertEquals(response.data['results'], self.data[20:])
        self.assertEquals(response.data['next'], None)
        self.assertNotEquals(response.data['previous'], None)
