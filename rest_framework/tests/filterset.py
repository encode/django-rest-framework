from __future__ import unicode_literals
import datetime
from decimal import Decimal
from django.test import TestCase
from django.test.client import RequestFactory
from django.utils import unittest
from rest_framework import generics, status, filters
from rest_framework.compat import django_filters
from rest_framework.tests.models import FilterableItem, BasicModel

factory = RequestFactory()


if django_filters:
    # Basic filter on a list view.
    class FilterFieldsRootView(generics.ListCreateAPIView):
        model = FilterableItem
        filter_fields = ['decimal', 'date']
        filter_backend = filters.DjangoFilterBackend

    # These class are used to test a filter class.
    class SeveralFieldsFilter(django_filters.FilterSet):
        text = django_filters.CharFilter(lookup_type='icontains')
        decimal = django_filters.NumberFilter(lookup_type='lt')
        date = django_filters.DateFilter(lookup_type='gt')

        class Meta:
            model = FilterableItem
            fields = ['text', 'decimal', 'date']

    class FilterClassRootView(generics.ListCreateAPIView):
        model = FilterableItem
        filter_class = SeveralFieldsFilter
        filter_backend = filters.DjangoFilterBackend

    # These classes are used to test a misconfigured filter class.
    class MisconfiguredFilter(django_filters.FilterSet):
        text = django_filters.CharFilter(lookup_type='icontains')

        class Meta:
            model = BasicModel
            fields = ['text']

    class IncorrectlyConfiguredRootView(generics.ListCreateAPIView):
        model = FilterableItem
        filter_class = MisconfiguredFilter
        filter_backend = filters.DjangoFilterBackend


class IntegrationTestFiltering(TestCase):
    """
    Integration tests for filtered list views.
    """

    def setUp(self):
        """
        Create 10 FilterableItem instances.
        """
        base_data = ('a', Decimal('0.25'), datetime.date(2012, 10, 8))
        for i in range(10):
            text = chr(i + ord(base_data[0])) * 3  # Produces string 'aaa', 'bbb', etc.
            decimal = base_data[1] + i
            date = base_data[2] - datetime.timedelta(days=i * 2)
            FilterableItem(text=text, decimal=decimal, date=date).save()

        self.objects = FilterableItem.objects
        self.data = [
            {'id': obj.id, 'text': obj.text, 'decimal': obj.decimal, 'date': obj.date.isoformat()}
            for obj in self.objects.all()
        ]

    @unittest.skipUnless(django_filters, 'django-filters not installed')
    def test_get_filtered_fields_root_view(self):
        """
        GET requests to paginated ListCreateAPIView should return paginated results.
        """
        view = FilterFieldsRootView.as_view()

        # Basic test with no filter.
        request = factory.get('/')
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

        # Tests that the decimal filter works.
        search_decimal = Decimal('2.25')
        request = factory.get('/?decimal=%s' % search_decimal)
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if f['decimal'] == search_decimal]
        self.assertEqual(response.data, expected_data)

        # Tests that the date filter works.
        search_date = datetime.date(2012, 9, 22)
        request = factory.get('/?date=%s' % search_date)  # search_date str: '2012-09-22'
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if datetime.datetime.strptime(f['date'], '%Y-%m-%d').date() == search_date]
        self.assertEqual(response.data, expected_data)

    @unittest.skipUnless(django_filters, 'django-filters not installed')
    def test_get_filtered_class_root_view(self):
        """
        GET requests to filtered ListCreateAPIView that have a filter_class set
        should return filtered results.
        """
        view = FilterClassRootView.as_view()

        # Basic test with no filter.
        request = factory.get('/')
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

        # Tests that the decimal filter set with 'lt' in the filter class works.
        search_decimal = Decimal('4.25')
        request = factory.get('/?decimal=%s' % search_decimal)
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if f['decimal'] < search_decimal]
        self.assertEqual(response.data, expected_data)

        # Tests that the date filter set with 'gt' in the filter class works.
        search_date = datetime.date(2012, 10, 2)
        request = factory.get('/?date=%s' % search_date)  # search_date str: '2012-10-02'
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if datetime.datetime.strptime(f['date'], '%Y-%m-%d').date() > search_date]
        self.assertEqual(response.data, expected_data)

        # Tests that the text filter set with 'icontains' in the filter class works.
        search_text = 'ff'
        request = factory.get('/?text=%s' % search_text)
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if search_text in f['text'].lower()]
        self.assertEqual(response.data, expected_data)

        # Tests that multiple filters works.
        search_decimal = Decimal('5.25')
        search_date = datetime.date(2012, 10, 2)
        request = factory.get('/?decimal=%s&date=%s' % (search_decimal, search_date))
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if
                         datetime.datetime.strptime(f['date'], '%Y-%m-%d').date() > search_date and
                         f['decimal'] < search_decimal]
        self.assertEqual(response.data, expected_data)

    @unittest.skipUnless(django_filters, 'django-filters not installed')
    def test_incorrectly_configured_filter(self):
        """
        An error should be displayed when the filter class is misconfigured.
        """
        view = IncorrectlyConfiguredRootView.as_view()

        request = factory.get('/')
        self.assertRaises(AssertionError, view, request)

    @unittest.skipUnless(django_filters, 'django-filters not installed')
    def test_unknown_filter(self):
        """
        GET requests with filters that aren't configured should return 200.
        """
        view = FilterFieldsRootView.as_view()

        search_integer = 10
        request = factory.get('/?integer=%s' % search_integer)
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
