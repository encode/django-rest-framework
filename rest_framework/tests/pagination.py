from django.core.paginator import Paginator
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import generics, status, pagination
from rest_framework.tests.models import BasicModel

factory = RequestFactory()


class RootView(generics.ListCreateAPIView):
    """
    Example description for OPTIONS.
    """
    model = BasicModel
    paginate_by = 10


class IntegrationTestPagination(TestCase):
    """
    Integration tests for paginated list views.
    """

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
        GET requests to paginated ListCreateAPIView should return paginated results.
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


class UnitTestPagination(TestCase):
    """
    Unit tests for pagination of primative objects.
    """

    def setUp(self):
        self.objects = [char * 3 for char in 'abcdefghijklmnopqrstuvwxyz']
        paginator = Paginator(self.objects, 10)
        self.first_page = paginator.page(1)
        self.last_page = paginator.page(3)

    def test_native_pagination(self):
        serializer = pagination.PaginationSerializer(instance=self.first_page)
        self.assertEquals(serializer.data['count'], 26)
        self.assertEquals(serializer.data['next'], '?page=2')
        self.assertEquals(serializer.data['previous'], None)
        self.assertEquals(serializer.data['results'], self.objects[:10])

        serializer = pagination.PaginationSerializer(instance=self.last_page)
        self.assertEquals(serializer.data['count'], 26)
        self.assertEquals(serializer.data['next'], None)
        self.assertEquals(serializer.data['previous'], '?page=2')
        self.assertEquals(serializer.data['results'], self.objects[20:])
