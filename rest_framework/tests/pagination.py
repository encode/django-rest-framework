import datetime
from decimal import Decimal
from django.core.paginator import Paginator
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import unittest
from rest_framework import generics, status, pagination, filters, serializers
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
    View for testing default paginate_by_param usage
    """
    model = BasicModel


class PaginateByParamView(generics.ListAPIView):
    """
    View for testing custom paginate_by_param usage
    """
    model = BasicModel
    paginate_by_param = 'page_size'


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


class PassOnContextPaginationSerializer(pagination.PaginationSerializer):
    class Meta:
        object_serializer_class = serializers.Serializer


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

    def test_context_available_in_result(self):
        """
        Ensure context gets passed through to the object serializer.
        """
        serializer = PassOnContextPaginationSerializer(self.first_page)
        serializer.data
        results = serializer.fields[serializer.results_field]
        self.assertTrue(serializer.context is results.context)


class TestUnpaginated(TestCase):
    """
    Tests for list views without pagination.
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

    def test_unpaginated(self):
        """
        Tests the default page size for this view.
        no page size --> no limit --> no meta data
        """
        request = factory.get('/')
        response = self.view(request)
        self.assertEquals(response.data, self.data)


class TestCustomPaginateByParam(TestCase):
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
        self.view = PaginateByParamView.as_view()

    def test_default_page_size(self):
        """
        Tests the default page size for this view.
        no page size --> no limit --> no meta data
        """
        request = factory.get('/')
        response = self.view(request).render()
        self.assertEquals(response.data, self.data)

    def test_paginate_by_param(self):
        """
        If paginate_by_param is set, the new kwarg should limit per view requests.
        """
        request = factory.get('/?page_size=5')
        response = self.view(request).render()
        self.assertEquals(response.data['count'], 13)
        self.assertEquals(response.data['results'], self.data[:5])


class CustomField(serializers.Field):
    def to_native(self, value):
        if not 'view' in self.context:
            raise RuntimeError("context isn't getting passed into custom field")
        return "value"


class BasicModelSerializer(serializers.Serializer):
    text = CustomField()


class TestContextPassedToCustomField(TestCase):
    def setUp(self):
        BasicModel.objects.create(text='ala ma kota')

    def test_with_pagination(self):
        class ListView(generics.ListCreateAPIView):
            model = BasicModel
            serializer_class = BasicModelSerializer
            paginate_by = 1

        self.view = ListView.as_view()
        request = factory.get('/')
        response = self.view(request).render()

        self.assertEquals(response.status_code, status.HTTP_200_OK)

