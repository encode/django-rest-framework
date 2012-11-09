import datetime
from decimal import Decimal
from django.core.paginator import Paginator
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import unittest
from rest_framework import generics, status, pagination, filters
from rest_framework.compat import django_filters
from rest_framework.tests.models import BasicModel, FilterableItem

factory = RequestFactory()


class RootView(generics.ListCreateAPIView):
    """
    Example description for OPTIONS.
    """
    model = BasicModel
    paginate_by = 10


if django_filters:
    class DecimalFilter(django_filters.FilterSet):
        decimal = django_filters.NumberFilter(lookup_type='lt')

        class Meta:
            model = FilterableItem
            fields = ['text', 'decimal', 'date']

    class FilterFieldsRootView(generics.ListCreateAPIView):
        model = FilterableItem
        paginate_by = 10
        filter_class = DecimalFilter
        filter_backend = filters.DjangoFilterBackend


class IntegrationTestPagination(TestCase):
    """
    Integration tests for paginated list views.
    """

    def setUp(self):
        """
        Create 26 BasicModel instances.
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


class IntegrationTestPaginationAndFiltering(TestCase):

    def setUp(self):
        """
        Create 50 FilterableItem instances.
        """
        base_data = ('a', Decimal('0.25'), datetime.date(2012, 10, 8))
        for i in range(26):
            text = chr(i + ord(base_data[0])) * 3  # Produces string 'aaa', 'bbb', etc.
            decimal = base_data[1] + i
            date = base_data[2] - datetime.timedelta(days=i * 2)
            FilterableItem(text=text, decimal=decimal, date=date).save()

        self.objects = FilterableItem.objects
        self.data = [
        {'id': obj.id, 'text': obj.text, 'decimal': obj.decimal, 'date': obj.date}
        for obj in self.objects.all()
        ]
        self.view = FilterFieldsRootView.as_view()

    @unittest.skipUnless(django_filters, 'django-filters not installed')
    def test_get_paginated_filtered_root_view(self):
        """
        GET requests to paginated filtered ListCreateAPIView should return
        paginated results. The next and previous links should preserve the
        filtered parameters.
        """
        request = factory.get('/?decimal=15.20')
        response = self.view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 15)
        self.assertEquals(response.data['results'], self.data[:10])
        self.assertNotEquals(response.data['next'], None)
        self.assertEquals(response.data['previous'], None)

        request = factory.get(response.data['next'])
        response = self.view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 15)
        self.assertEquals(response.data['results'], self.data[10:15])
        self.assertEquals(response.data['next'], None)
        self.assertNotEquals(response.data['previous'], None)

        request = factory.get(response.data['previous'])
        response = self.view(request).render()
        self.assertEquals(response.status_code, status.HTTP_200_OK)
        self.assertEquals(response.data['count'], 15)
        self.assertEquals(response.data['results'], self.data[:10])
        self.assertNotEquals(response.data['next'], None)
        self.assertEquals(response.data['previous'], None)


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
        serializer = pagination.PaginationSerializer(self.first_page)
        self.assertEquals(serializer.data['count'], 26)
        self.assertEquals(serializer.data['next'], '?page=2')
        self.assertEquals(serializer.data['previous'], None)
        self.assertEquals(serializer.data['results'], self.objects[:10])

        serializer = pagination.PaginationSerializer(self.last_page)
        self.assertEquals(serializer.data['count'], 26)
        self.assertEquals(serializer.data['next'], None)
        self.assertEquals(serializer.data['previous'], '?page=2')
        self.assertEquals(serializer.data['results'], self.objects[20:])
