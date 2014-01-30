from __future__ import unicode_literals
import datetime
from decimal import Decimal
from django.db import models
from django.core.paginator import Paginator
from django.test import TestCase
from django.utils import unittest
from rest_framework import generics, status, pagination, filters, serializers
from rest_framework.compat import django_filters
from rest_framework.test import APIRequestFactory
from rest_framework.tests.models import BasicModel
from .models import FilterableItem

factory = APIRequestFactory()

# Helper function to split arguments out of an url
def split_arguments_from_url(url):
    if '?' not in url:
        return url

    path, args = url.split('?')
    args = dict(r.split('=') for r in args.split('&'))
    return path, args


class RootView(generics.ListCreateAPIView):
    """
    Example description for OPTIONS.
    """
    model = BasicModel
    paginate_by = 10


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


class MaxPaginateByView(generics.ListAPIView):
    """
    View for testing custom max_paginate_by usage
    """
    model = BasicModel
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
            {'id': obj.id, 'text': obj.text, 'decimal': obj.decimal, 'date': obj.date}
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
            model = FilterableItem
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
            model = FilterableItem
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
        self.assertEqual(serializer.data['count'], 26)
        self.assertEqual(serializer.data['next'], '?page=2')
        self.assertEqual(serializer.data['previous'], None)
        self.assertEqual(serializer.data['results'], self.objects[:10])

        serializer = pagination.PaginationSerializer(self.last_page)
        self.assertEqual(serializer.data['count'], 26)
        self.assertEqual(serializer.data['next'], None)
        self.assertEqual(serializer.data['previous'], '?page=2')
        self.assertEqual(serializer.data['results'], self.objects[20:])

    def test_context_available_in_result(self):
        """
        Ensure context gets passed through to the object serializer.
        """
        serializer = PassOnContextPaginationSerializer(self.first_page, context={'foo': 'bar'})
        serializer.data
        results = serializer.fields[serializer.results_field]
        self.assertEqual(serializer.context, results.context)


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


### Tests for context in pagination serializers

class CustomField(serializers.Field):
    def to_native(self, value):
        if not 'view' in self.context:
            raise RuntimeError("context isn't getting passed into custom field")
        return "value"


class BasicModelSerializer(serializers.Serializer):
    text = CustomField()

    def __init__(self, *args, **kwargs):
        super(BasicModelSerializer, self).__init__(*args, **kwargs)
        if not 'view' in self.context:
            raise RuntimeError("context isn't getting passed into serializer init")


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

        self.assertEqual(response.status_code, status.HTTP_200_OK)


### Tests for custom pagination serializers

class LinksSerializer(serializers.Serializer):
    next = pagination.NextPageField(source='*')
    prev = pagination.PreviousPageField(source='*')


class CustomPaginationSerializer(pagination.BasePaginationSerializer):
    links = LinksSerializer(source='*')  # Takes the page object as the source
    total_results = serializers.Field(source='paginator.count')

    results_field = 'objects'


class TestCustomPaginationSerializer(TestCase):
    def setUp(self):
        objects = ['john', 'paul', 'george', 'ringo']
        paginator = Paginator(objects, 2)
        self.page = paginator.page(1)

    def test_custom_pagination_serializer(self):
        request = APIRequestFactory().get('/foobar')
        serializer = CustomPaginationSerializer(
            instance=self.page,
            context={'request': request}
        )
        expected = {
            'links': {
                'next': 'http://testserver/foobar?page=2',
                'prev': None
            },
            'total_results': 4,
            'objects': ['john', 'paul']
        }
        self.assertEqual(serializer.data, expected)


class NonIntegerPage(object):

    def __init__(self, paginator, object_list, prev_token, token, next_token):
        self.paginator = paginator
        self.object_list = object_list
        self.prev_token = prev_token
        self.token = token
        self.next_token = next_token

    def has_next(self):
        return not not self.next_token

    def next_page_number(self):
        return self.next_token

    def has_previous(self):
        return not not self.prev_token

    def previous_page_number(self):
        return self.prev_token


class NonIntegerPaginator(object):

    def __init__(self, object_list, per_page):
        self.object_list = object_list
        self.per_page = per_page

    def count(self):
        # pretend like we don't know how many pages we have
        return None

    def page(self, token=None):
        if token:
            try:
                first = self.object_list.index(token)
            except ValueError:
                first = 0
        else:
            first = 0
        n = len(self.object_list)
        last = min(first + self.per_page, n)
        prev_token = self.object_list[last - (2 * self.per_page)] if first else None
        next_token = self.object_list[last] if last < n else None
        return NonIntegerPage(self, self.object_list[first:last], prev_token, token, next_token)


class TestNonIntegerPagination(TestCase):


    def test_custom_pagination_serializer(self):
        objects = ['john', 'paul', 'george', 'ringo']
        paginator = NonIntegerPaginator(objects, 2)

        request = APIRequestFactory().get('/foobar')
        serializer = CustomPaginationSerializer(
            instance=paginator.page(),
            context={'request': request}
        )
        expected = {
            'links': {
                'next': 'http://testserver/foobar?page={0}'.format(objects[2]),
                'prev': None
            },
            'total_results': None,
            'objects': objects[:2]
        }
        self.assertEqual(serializer.data, expected)

        request = APIRequestFactory().get('/foobar')
        serializer = CustomPaginationSerializer(
            instance=paginator.page('george'),
            context={'request': request}
        )
        expected = {
            'links': {
                'next': None,
                'prev': 'http://testserver/foobar?page={0}'.format(objects[0]),
            },
            'total_results': None,
            'objects': objects[2:]
        }
        self.assertEqual(serializer.data, expected)
