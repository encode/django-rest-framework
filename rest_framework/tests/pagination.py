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


class DefaultPageSizeKwargView(generics.ListAPIView):
    """
    View for testing default page_size usage
    """
    model = BasicModel


class CustomPageSizeKwargView(generics.ListAPIView):
    """
    View for testing custom page_size usage
    """
    model = BasicModel
    page_size_kwarg = 'ps'


class NonePageSizeKwargView(generics.ListAPIView):
    """
    View for testing None page_size usage
    """
    model = BasicModel
    page_size_kwarg = None


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
    Unit tests for pagination of primitive objects.
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


class TestDefaultPageSizeKwarg(TestCase):
    """
    Tests for list views with default page size kwarg
    """

    def setUp(self):
        """
        Create 13 BasicModel instances.
        """
        for i in range(13):
            BasicModel(text=i).save()
        self.objects = BasicModel.objects
        self.data = [
        {'id': obj.id, 'text': obj.text}
        for obj in self.objects.all()
        ]
        self.view = DefaultPageSizeKwargView.as_view()

    def test_default_page_size(self):
        """
        Tests the default page size for this view.
        no page size --> no limit --> no meta data
        """
        request = factory.get('/')
        response = self.view(request).render()
        self.assertEquals(response.data, self.data)

    def test_default_page_size_kwarg(self):
        """
        If page_size_kwarg is set not set, the default page_size kwarg should limit per view requests.
        """
        request = factory.get('/?page_size=5')
        response = self.view(request).render()
        self.assertEquals(response.data['count'], 13)
        self.assertEquals(response.data['results'], self.data[:5])


class TestCustomPageSizeKwarg(TestCase):
    """
    Tests for list views with default page size kwarg
    """

    def setUp(self):
        """
        Create 13 BasicModel instances.
        """
        for i in range(13):
            BasicModel(text=i).save()
        self.objects = BasicModel.objects
        self.data = [
        {'id': obj.id, 'text': obj.text}
        for obj in self.objects.all()
        ]
        self.view = CustomPageSizeKwargView.as_view()

    def test_default_page_size(self):
        """
        Tests the default page size for this view.
        no page size --> no limit --> no meta data
        """
        request = factory.get('/')
        response = self.view(request).render()
        self.assertEquals(response.data, self.data)

    def test_disabled_default_page_size_kwarg(self):
        """
        If page_size_kwarg is set set, the default page_size kwarg should not work.
        """
        request = factory.get('/?page_size=5')
        response = self.view(request).render()
        self.assertEquals(response.data, self.data)

    def test_custom_page_size_kwarg(self):
        """
        If page_size_kwarg is set set, the new kwarg should limit per view requests.
        """
        request = factory.get('/?ps=5')
        response = self.view(request).render()
        self.assertEquals(response.data['count'], 13)
        self.assertEquals(response.data['results'], self.data[:5])


class TestNonePageSizeKwarg(TestCase):
    """
    Tests for list views with default page size kwarg
    """

    def setUp(self):
        """
        Create 13 BasicModel instances.
        """
        for i in range(13):
            BasicModel(text=i).save()
        self.objects = BasicModel.objects
        self.data = [
        {'id': obj.id, 'text': obj.text}
        for obj in self.objects.all()
        ]
        self.view = NonePageSizeKwargView.as_view()

    def test_default_page_size(self):
        """
        Tests the default page size for this view.
        no page size --> no limit --> no meta data
        """
        request = factory.get('/')
        response = self.view(request).render()
        self.assertEquals(response.data, self.data)

    def test_none_page_size_kwarg(self):
        """
        If page_size_kwarg is set to None, custom page_size per request should be disabled.
        """
        request = factory.get('/?page_size=5')
        response = self.view(request).render()
        self.assertEquals(response.data, self.data)
