from __future__ import unicode_literals
import datetime
from decimal import Decimal
from django.db import models
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils import unittest
from rest_framework import generics, serializers, status, filters
from rest_framework.compat import django_filters, patterns, url
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from .models import FilterableItem, BasicModel
from .utils import temporary_setting

factory = APIRequestFactory()


if django_filters:
    # Basic filter on a list view.
    class FilterFieldsRootView(generics.ListCreateAPIView):
        model = FilterableItem
        filter_fields = ['decimal', 'date']
        filter_backends = (filters.DjangoFilterBackend,)

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
        filter_backends = (filters.DjangoFilterBackend,)

    # These classes are used to test a misconfigured filter class.
    class MisconfiguredFilter(django_filters.FilterSet):
        text = django_filters.CharFilter(lookup_type='icontains')

        class Meta:
            model = BasicModel
            fields = ['text']

    class IncorrectlyConfiguredRootView(generics.ListCreateAPIView):
        model = FilterableItem
        filter_class = MisconfiguredFilter
        filter_backends = (filters.DjangoFilterBackend,)

    class FilterClassDetailView(generics.RetrieveAPIView):
        model = FilterableItem
        filter_class = SeveralFieldsFilter
        filter_backends = (filters.DjangoFilterBackend,)

    # Regression test for #814
    class FilterableItemSerializer(serializers.ModelSerializer):
        class Meta:
            model = FilterableItem

    class FilterFieldsQuerysetView(generics.ListCreateAPIView):
        queryset = FilterableItem.objects.all()
        serializer_class = FilterableItemSerializer
        filter_fields = ['decimal', 'date']
        filter_backends = (filters.DjangoFilterBackend,)

    class GetQuerysetView(generics.ListCreateAPIView):
        serializer_class = FilterableItemSerializer
        filter_class = SeveralFieldsFilter
        filter_backends = (filters.DjangoFilterBackend,)

        def get_queryset(self):
            return FilterableItem.objects.all()

    urlpatterns = patterns('',
        url(r'^(?P<pk>\d+)/$', FilterClassDetailView.as_view(), name='detail-view'),
        url(r'^$', FilterClassRootView.as_view(), name='root-view'),
        url(r'^get-queryset/$', GetQuerysetView.as_view(),
            name='get-queryset-view'),
    )


class CommonFilteringTestCase(TestCase):
    def _serialize_object(self, obj):
        return {'id': obj.id, 'text': obj.text, 'decimal': obj.decimal, 'date': obj.date}

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
            self._serialize_object(obj)
            for obj in self.objects.all()
        ]


class IntegrationTestFiltering(CommonFilteringTestCase):
    """
    Integration tests for filtered list views.
    """

    @unittest.skipUnless(django_filters, 'django-filter not installed')
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
        request = factory.get('/', {'decimal': '%s' % search_decimal})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if f['decimal'] == search_decimal]
        self.assertEqual(response.data, expected_data)

        # Tests that the date filter works.
        search_date = datetime.date(2012, 9, 22)
        request = factory.get('/', {'date': '%s' % search_date})  # search_date str: '2012-09-22'
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if f['date'] == search_date]
        self.assertEqual(response.data, expected_data)

    @unittest.skipUnless(django_filters, 'django-filter not installed')
    def test_filter_with_queryset(self):
        """
        Regression test for #814.
        """
        view = FilterFieldsQuerysetView.as_view()

        # Tests that the decimal filter works.
        search_decimal = Decimal('2.25')
        request = factory.get('/', {'decimal': '%s' % search_decimal})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if f['decimal'] == search_decimal]
        self.assertEqual(response.data, expected_data)

    @unittest.skipUnless(django_filters, 'django-filter not installed')
    def test_filter_with_get_queryset_only(self):
        """
        Regression test for #834.
        """
        view = GetQuerysetView.as_view()
        request = factory.get('/get-queryset/')
        view(request).render()
        # Used to raise "issubclass() arg 2 must be a class or tuple of classes"
        # here when neither `model' nor `queryset' was specified.

    @unittest.skipUnless(django_filters, 'django-filter not installed')
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
        request = factory.get('/', {'decimal': '%s' % search_decimal})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if f['decimal'] < search_decimal]
        self.assertEqual(response.data, expected_data)

        # Tests that the date filter set with 'gt' in the filter class works.
        search_date = datetime.date(2012, 10, 2)
        request = factory.get('/', {'date': '%s' % search_date})  # search_date str: '2012-10-02'
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if f['date'] > search_date]
        self.assertEqual(response.data, expected_data)

        # Tests that the text filter set with 'icontains' in the filter class works.
        search_text = 'ff'
        request = factory.get('/', {'text': '%s' % search_text})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if search_text in f['text'].lower()]
        self.assertEqual(response.data, expected_data)

        # Tests that multiple filters works.
        search_decimal = Decimal('5.25')
        search_date = datetime.date(2012, 10, 2)
        request = factory.get('/', {
            'decimal': '%s' % (search_decimal,),
            'date': '%s' % (search_date,)
        })
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = [f for f in self.data if f['date'] > search_date and
                         f['decimal'] < search_decimal]
        self.assertEqual(response.data, expected_data)

    @unittest.skipUnless(django_filters, 'django-filter not installed')
    def test_incorrectly_configured_filter(self):
        """
        An error should be displayed when the filter class is misconfigured.
        """
        view = IncorrectlyConfiguredRootView.as_view()

        request = factory.get('/')
        self.assertRaises(AssertionError, view, request)

    @unittest.skipUnless(django_filters, 'django-filter not installed')
    def test_unknown_filter(self):
        """
        GET requests with filters that aren't configured should return 200.
        """
        view = FilterFieldsRootView.as_view()

        search_integer = 10
        request = factory.get('/', {'integer': '%s' % search_integer})
        response = view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class IntegrationTestDetailFiltering(CommonFilteringTestCase):
    """
    Integration tests for filtered detail views.
    """
    urls = 'tests.test_filters'

    def _get_url(self, item):
        return reverse('detail-view', kwargs=dict(pk=item.pk))

    @unittest.skipUnless(django_filters, 'django-filter not installed')
    def test_get_filtered_detail_view(self):
        """
        GET requests to filtered RetrieveAPIView that have a filter_class set
        should return filtered results.
        """
        item = self.objects.all()[0]
        data = self._serialize_object(item)

        # Basic test with no filter.
        response = self.client.get(self._get_url(item))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, data)

        # Tests that the decimal filter set that should fail.
        search_decimal = Decimal('4.25')
        high_item = self.objects.filter(decimal__gt=search_decimal)[0]
        response = self.client.get(
            '{url}'.format(url=self._get_url(high_item)),
            {'decimal': '{param}'.format(param=search_decimal)})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Tests that the decimal filter set that should succeed.
        search_decimal = Decimal('4.25')
        low_item = self.objects.filter(decimal__lt=search_decimal)[0]
        low_item_data = self._serialize_object(low_item)
        response = self.client.get(
            '{url}'.format(url=self._get_url(low_item)),
            {'decimal': '{param}'.format(param=search_decimal)})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, low_item_data)

        # Tests that multiple filters works.
        search_decimal = Decimal('5.25')
        search_date = datetime.date(2012, 10, 2)
        valid_item = self.objects.filter(decimal__lt=search_decimal, date__gt=search_date)[0]
        valid_item_data = self._serialize_object(valid_item)
        response = self.client.get(
            '{url}'.format(url=self._get_url(valid_item)), {
                'decimal': '{decimal}'.format(decimal=search_decimal),
                'date': '{date}'.format(date=search_date)
            })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, valid_item_data)


class SearchFilterModel(models.Model):
    title = models.CharField(max_length=20)
    text = models.CharField(max_length=100)


class SearchFilterTests(TestCase):
    def setUp(self):
        # Sequence of title/text is:
        #
        # z   abc
        # zz  bcd
        # zzz cde
        # ...
        for idx in range(10):
            title = 'z' * (idx + 1)
            text = (
                chr(idx + ord('a')) +
                chr(idx + ord('b')) +
                chr(idx + ord('c'))
            )
            SearchFilterModel(title=title, text=text).save()

    def test_search(self):
        class SearchListView(generics.ListAPIView):
            model = SearchFilterModel
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', 'text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'b'})
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 1, 'title': 'z', 'text': 'abc'},
                {'id': 2, 'title': 'zz', 'text': 'bcd'}
            ]
        )

    def test_exact_search(self):
        class SearchListView(generics.ListAPIView):
            model = SearchFilterModel
            filter_backends = (filters.SearchFilter,)
            search_fields = ('=title', 'text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'zzz'})
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 3, 'title': 'zzz', 'text': 'cde'}
            ]
        )

    def test_startswith_search(self):
        class SearchListView(generics.ListAPIView):
            model = SearchFilterModel
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', '^text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'b'})
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 2, 'title': 'zz', 'text': 'bcd'}
            ]
        )

    def test_search_with_nonstandard_search_param(self):
        with temporary_setting('SEARCH_PARAM', 'query', module=filters):
            class SearchListView(generics.ListAPIView):
                model = SearchFilterModel
                filter_backends = (filters.SearchFilter,)
                search_fields = ('title', 'text')

            view = SearchListView.as_view()
            request = factory.get('/', {'query': 'b'})
            response = view(request)
            self.assertEqual(
                response.data,
                [
                    {'id': 1, 'title': 'z', 'text': 'abc'},
                    {'id': 2, 'title': 'zz', 'text': 'bcd'}
                ]
            )


class OrdringFilterModel(models.Model):
    title = models.CharField(max_length=20)
    text = models.CharField(max_length=100)


class OrderingFilterRelatedModel(models.Model):
    related_object = models.ForeignKey(OrdringFilterModel,
                                       related_name="relateds")


class OrderingFilterTests(TestCase):
    def setUp(self):
        # Sequence of title/text is:
        #
        # zyx abc
        # yxw bcd
        # xwv cde
        for idx in range(3):
            title = (
                chr(ord('z') - idx) +
                chr(ord('y') - idx) +
                chr(ord('x') - idx)
            )
            text = (
                chr(idx + ord('a')) +
                chr(idx + ord('b')) +
                chr(idx + ord('c'))
            )
            OrdringFilterModel(title=title, text=text).save()

    def test_ordering(self):
        class OrderingListView(generics.ListAPIView):
            model = OrdringFilterModel
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'text'})
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 1, 'title': 'zyx', 'text': 'abc'},
                {'id': 2, 'title': 'yxw', 'text': 'bcd'},
                {'id': 3, 'title': 'xwv', 'text': 'cde'},
            ]
        )

    def test_reverse_ordering(self):
        class OrderingListView(generics.ListAPIView):
            model = OrdringFilterModel
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': '-text'})
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 3, 'title': 'xwv', 'text': 'cde'},
                {'id': 2, 'title': 'yxw', 'text': 'bcd'},
                {'id': 1, 'title': 'zyx', 'text': 'abc'},
            ]
        )

    def test_incorrectfield_ordering(self):
        class OrderingListView(generics.ListAPIView):
            model = OrdringFilterModel
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'foobar'})
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 3, 'title': 'xwv', 'text': 'cde'},
                {'id': 2, 'title': 'yxw', 'text': 'bcd'},
                {'id': 1, 'title': 'zyx', 'text': 'abc'},
            ]
        )

    def test_default_ordering(self):
        class OrderingListView(generics.ListAPIView):
            model = OrdringFilterModel
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            oredering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('')
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 3, 'title': 'xwv', 'text': 'cde'},
                {'id': 2, 'title': 'yxw', 'text': 'bcd'},
                {'id': 1, 'title': 'zyx', 'text': 'abc'},
            ]
        )

    def test_default_ordering_using_string(self):
        class OrderingListView(generics.ListAPIView):
            model = OrdringFilterModel
            filter_backends = (filters.OrderingFilter,)
            ordering = 'title'
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('')
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 3, 'title': 'xwv', 'text': 'cde'},
                {'id': 2, 'title': 'yxw', 'text': 'bcd'},
                {'id': 1, 'title': 'zyx', 'text': 'abc'},
            ]
        )

    def test_ordering_by_aggregate_field(self):
        # create some related models to aggregate order by
        num_objs = [2, 5, 3]
        for obj, num_relateds in zip(OrdringFilterModel.objects.all(),
                                     num_objs):
            for _ in range(num_relateds):
                new_related = OrderingFilterRelatedModel(
                    related_object=obj
                )
                new_related.save()

        class OrderingListView(generics.ListAPIView):
            model = OrdringFilterModel
            filter_backends = (filters.OrderingFilter,)
            ordering = 'title'
            ordering_fields = '__all__'
            queryset = OrdringFilterModel.objects.all().annotate(
                models.Count("relateds"))

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'relateds__count'})
        response = view(request)
        self.assertEqual(
            response.data,
            [
                {'id': 1, 'title': 'zyx', 'text': 'abc'},
                {'id': 3, 'title': 'xwv', 'text': 'cde'},
                {'id': 2, 'title': 'yxw', 'text': 'bcd'},
            ]
        )

    def test_ordering_with_nonstandard_ordering_param(self):
        with temporary_setting('ORDERING_PARAM', 'order', filters):
            class OrderingListView(generics.ListAPIView):
                model = OrdringFilterModel
                filter_backends = (filters.OrderingFilter,)
                ordering = ('title',)
                ordering_fields = ('text',)

            view = OrderingListView.as_view()
            request = factory.get('/', {'order': 'text'})
            response = view(request)
            self.assertEqual(
                response.data,
                [
                    {'id': 1, 'title': 'zyx', 'text': 'abc'},
                    {'id': 2, 'title': 'yxw', 'text': 'bcd'},
                    {'id': 3, 'title': 'xwv', 'text': 'cde'},
                ]
            )


class SensitiveOrderingFilterModel(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=100)


# Three different styles of serializer.
# All should allow ordering by username, but not by password.
class SensitiveDataSerializer1(serializers.ModelSerializer):
    username = serializers.CharField()

    class Meta:
        model = SensitiveOrderingFilterModel
        fields = ('id', 'username')


class SensitiveDataSerializer2(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = SensitiveOrderingFilterModel
        fields = ('id', 'username', 'password')


class SensitiveDataSerializer3(serializers.ModelSerializer):
    user = serializers.CharField(source='username')

    class Meta:
        model = SensitiveOrderingFilterModel
        fields = ('id', 'user')


class SensitiveOrderingFilterTests(TestCase):
    def setUp(self):
        for idx in range(3):
            username = {0: 'userA', 1: 'userB', 2: 'userC'}[idx]
            password = {0: 'passA', 1: 'passC', 2: 'passB'}[idx]
            SensitiveOrderingFilterModel(username=username, password=password).save()

    def test_order_by_serializer_fields(self):
        for serializer_cls in [
            SensitiveDataSerializer1,
            SensitiveDataSerializer2,
            SensitiveDataSerializer3
        ]:
            class OrderingListView(generics.ListAPIView):
                queryset = SensitiveOrderingFilterModel.objects.all().order_by('username')
                filter_backends = (filters.OrderingFilter,)
                serializer_class = serializer_cls

            view = OrderingListView.as_view()
            request = factory.get('/', {'ordering': '-username'})
            response = view(request)

            if serializer_cls == SensitiveDataSerializer3:
                username_field = 'user'
            else:
                username_field = 'username'

            # Note: Inverse username ordering correctly applied.
            self.assertEqual(
                response.data,
                [
                    {'id': 3, username_field: 'userC'},
                    {'id': 2, username_field: 'userB'},
                    {'id': 1, username_field: 'userA'},
                ]
            )

    def test_cannot_order_by_non_serializer_fields(self):
        for serializer_cls in [
            SensitiveDataSerializer1,
            SensitiveDataSerializer2,
            SensitiveDataSerializer3
        ]:
            class OrderingListView(generics.ListAPIView):
                queryset = SensitiveOrderingFilterModel.objects.all().order_by('username')
                filter_backends = (filters.OrderingFilter,)
                serializer_class = serializer_cls

            view = OrderingListView.as_view()
            request = factory.get('/', {'ordering': 'password'})
            response = view(request)

            if serializer_cls == SensitiveDataSerializer3:
                username_field = 'user'
            else:
                username_field = 'username'

            # Note: The passwords are not in order.  Default ordering is used.
            self.assertEqual(
                response.data,
                [
                    {'id': 1, username_field: 'userA'}, # PassB
                    {'id': 2, username_field: 'userB'}, # PassC
                    {'id': 3, username_field: 'userC'}, # PassA
                ]
            )
