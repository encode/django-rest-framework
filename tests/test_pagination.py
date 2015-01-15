from __future__ import unicode_literals
import datetime
from decimal import Decimal
from django.test import TestCase
from django.utils import unittest
from rest_framework import generics, pagination, serializers, status, filters
from rest_framework.compat import django_filters
from rest_framework.request import Request
from rest_framework.pagination import PageLink, PAGE_BREAK
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


class TestLimitOffset:
    def setup(self):
        self.pagination = pagination.LimitOffsetPagination()
        self.queryset = range(1, 101)

    def paginate_queryset(self, request):
        return self.pagination.paginate_queryset(self.queryset, request)

    def get_paginated_content(self, queryset):
        response = self.pagination.get_paginated_response(queryset)
        return response.data

    def get_html_context(self):
        return self.pagination.get_html_context()

    def test_no_offset(self):
        request = Request(factory.get('/', {'limit': 5}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [1, 2, 3, 4, 5]
        assert content == {
            'results': [1, 2, 3, 4, 5],
            'previous': None,
            'next': 'http://testserver/?limit=5&offset=5',
            'count': 100
        }
        assert context == {
            'previous_url': None,
            'next_url': 'http://testserver/?limit=5&offset=5',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, True, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, False, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ]
        }

    def test_first_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 5}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [6, 7, 8, 9, 10]
        assert content == {
            'results': [6, 7, 8, 9, 10],
            'previous': 'http://testserver/?limit=5',
            'next': 'http://testserver/?limit=5&offset=10',
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/?limit=5',
            'next_url': 'http://testserver/?limit=5&offset=10',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, True, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ]
        }

    def test_middle_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 10}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [11, 12, 13, 14, 15]
        assert content == {
            'results': [11, 12, 13, 14, 15],
            'previous': 'http://testserver/?limit=5&offset=5',
            'next': 'http://testserver/?limit=5&offset=15',
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/?limit=5&offset=5',
            'next_url': 'http://testserver/?limit=5&offset=15',
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PageLink('http://testserver/?limit=5&offset=5', 2, False, False),
                PageLink('http://testserver/?limit=5&offset=10', 3, True, False),
                PageLink('http://testserver/?limit=5&offset=15', 4, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=95', 20, False, False),
            ]
        }

    def test_ending_offset(self):
        request = Request(factory.get('/', {'limit': 5, 'offset': 95}))
        queryset = self.paginate_queryset(request)
        content = self.get_paginated_content(queryset)
        context = self.get_html_context()
        assert queryset == [96, 97, 98, 99, 100]
        assert content == {
            'results': [96, 97, 98, 99, 100],
            'previous': 'http://testserver/?limit=5&offset=90',
            'next': None,
            'count': 100
        }
        assert context == {
            'previous_url': 'http://testserver/?limit=5&offset=90',
            'next_url': None,
            'page_links': [
                PageLink('http://testserver/?limit=5', 1, False, False),
                PAGE_BREAK,
                PageLink('http://testserver/?limit=5&offset=85', 18, False, False),
                PageLink('http://testserver/?limit=5&offset=90', 19, False, False),
                PageLink('http://testserver/?limit=5&offset=95', 20, True, False),
            ]
        }
