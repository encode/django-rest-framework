from __future__ import unicode_literals
import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import unittest
from rest_framework import generics, serializers, status, filters
from rest_framework.compat import django_filters
from rest_framework.test import APIRequestFactory
from .models import BasicModel, FilterableItem

factory = APIRequestFactory()


# Helper function to split arguments out of an url
def split_arguments_from_url(url):
    if '?' not in url:
        return url

    path, args = url.split('?')
    args = dict(r.split('=') for r in args.split('&'))
    return path, args


class BasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel


class FilterableItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterableItem


class RootView(generics.ListCreateAPIView):
    """
    Example description for OPTIONS.
    """
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer
    paginate_by = 10


class DefaultPageSizeKwargView(generics.ListAPIView):
    """
    View for testing default paginate_by_param usage
    """
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer


class PaginateByParamView(generics.ListAPIView):
    """
    View for testing custom paginate_by_param usage
    """
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer
    paginate_by_param = 'page_size'


class MaxPaginateByView(generics.ListAPIView):
    """
    View for testing custom max_paginate_by usage
    """
    queryset = BasicModel.objects.all()
    serializer_class = BasicSerializer
    paginate_by = 3
    max_paginate_by = 5
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
        # Note: Database queries are a `SELECT COUNT`, and `SELECT <fields>`
        with self.assertNumQueries(2):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 26)
        self.assertEqual(response.data['results'], self.data[:10])
        self.assertNotEqual(response.data['next'], None)
        self.assertEqual(response.data['previous'], None)

        request = factory.get(*split_arguments_from_url(response.data['next']))
        with self.assertNumQueries(2):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 26)
        self.assertEqual(response.data['results'], self.data[10:20])
        self.assertNotEqual(response.data['next'], None)
        self.assertNotEqual(response.data['previous'], None)

        request = factory.get(*split_arguments_from_url(response.data['next']))
        with self.assertNumQueries(2):
            response = self.view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 26)
        self.assertEqual(response.data['results'], self.data[20:])
        self.assertEqual(response.data['next'], None)
        self.assertNotEqual(response.data['previous'], None)


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
            {'id': obj.id, 'text': obj.text, 'decimal': str(obj.decimal), 'date': obj.date.isoformat()}
            for obj in self.objects.all()
        ]

    @unittest.skipUnless(django_filters, 'django-filter not installed')
    def test_get_django_filter_paginated_filtered_root_view(self):
        """
        GET requests to paginated filtered ListCreateAPIView should return
        paginated results. The next and previous links should preserve the
        filtered parameters.
        """
        class DecimalFilter(django_filters.FilterSet):
            decimal = django_filters.NumberFilter(lookup_type='lt')

            class Meta:
                model = FilterableItem
                fields = ['text', 'decimal', 'date']

        class FilterFieldsRootView(generics.ListCreateAPIView):
            queryset = FilterableItem.objects.all()
            serializer_class = FilterableItemSerializer
            paginate_by = 10
            filter_class = DecimalFilter
            filter_backends = (filters.DjangoFilterBackend,)

        view = FilterFieldsRootView.as_view()

        EXPECTED_NUM_QUERIES = 2

        request = factory.get('/', {'decimal': '15.20'})
        with self.assertNumQueries(EXPECTED_NUM_QUERIES):
            response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(response.data['results'], self.data[:10])
        self.assertNotEqual(response.data['next'], None)
        self.assertEqual(response.data['previous'], None)

        request = factory.get(*split_arguments_from_url(response.data['next']))
        with self.assertNumQueries(EXPECTED_NUM_QUERIES):
            response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(response.data['results'], self.data[10:15])
        self.assertEqual(response.data['next'], None)
        self.assertNotEqual(response.data['previous'], None)

        request = factory.get(*split_arguments_from_url(response.data['previous']))
        with self.assertNumQueries(EXPECTED_NUM_QUERIES):
            response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(response.data['results'], self.data[:10])
        self.assertNotEqual(response.data['next'], None)
        self.assertEqual(response.data['previous'], None)

    def test_get_basic_paginated_filtered_root_view(self):
        """
        Same as `test_get_django_filter_paginated_filtered_root_view`,
        except using a custom filter backend instead of the django-filter
        backend,
        """

        class DecimalFilterBackend(filters.BaseFilterBackend):
            def filter_queryset(self, request, queryset, view):
                return queryset.filter(decimal__lt=Decimal(request.GET['decimal']))

        class BasicFilterFieldsRootView(generics.ListCreateAPIView):
            queryset = FilterableItem.objects.all()
            serializer_class = FilterableItemSerializer
            paginate_by = 10
            filter_backends = (DecimalFilterBackend,)

        view = BasicFilterFieldsRootView.as_view()

        request = factory.get('/', {'decimal': '15.20'})
        with self.assertNumQueries(2):
            response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(response.data['results'], self.data[:10])
        self.assertNotEqual(response.data['next'], None)
        self.assertEqual(response.data['previous'], None)

        request = factory.get(*split_arguments_from_url(response.data['next']))
        with self.assertNumQueries(2):
            response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(response.data['results'], self.data[10:15])
        self.assertEqual(response.data['next'], None)
        self.assertNotEqual(response.data['previous'], None)

        request = factory.get(*split_arguments_from_url(response.data['previous']))
        with self.assertNumQueries(2):
            response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 15)
        self.assertEqual(response.data['results'], self.data[:10])
        self.assertNotEqual(response.data['next'], None)
        self.assertEqual(response.data['previous'], None)


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
        self.assertEqual(response.data, self.data)


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
        self.assertEqual(response.data, self.data)

    def test_paginate_by_param(self):
        """
        If paginate_by_param is set, the new kwarg should limit per view requests.
        """
        request = factory.get('/', {'page_size': 5})
        response = self.view(request).render()
        self.assertEqual(response.data['count'], 13)
        self.assertEqual(response.data['results'], self.data[:5])


class TestMaxPaginateByParam(TestCase):
    """
    Tests for list views with max_paginate_by kwarg
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
        self.view = MaxPaginateByView.as_view()

    def test_max_paginate_by(self):
        """
        If max_paginate_by is set, it should limit page size for the view.
        """
        request = factory.get('/', data={'page_size': 10})
        response = self.view(request).render()
        self.assertEqual(response.data['count'], 13)
        self.assertEqual(response.data['results'], self.data[:5])

    def test_max_paginate_by_without_page_size_param(self):
        """
        If max_paginate_by is set, but client does not specifiy page_size,
        standard `paginate_by` behavior should be used.
        """
        request = factory.get('/')
        response = self.view(request).render()
        self.assertEqual(response.data['results'], self.data[:3])
