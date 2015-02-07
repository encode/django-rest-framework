#!/usr/bin/env python
# coding: utf-8
from decimal import Decimal
from datetime import datetime
from django.utils import unittest

from pytest import mark

from rest_framework import viewsets, serializers
from rest_framework.filters import DjangoFilterBackend
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter
from rest_framework.test import APITransactionTestCase
from tests.models import RegularFieldsAndFKModel2, RegularFieldsModel2


data = {
    'big_integer_field': 100000,
    'char_field': 'a',
    'comma_separated_integer_field': '1,2',
    'date_field': str(datetime.now().date()),
    'datetime_field': str(datetime.now()),
    'decimal_field': str(Decimal('1.5')),
    'email_field': 'somewhere@overtherainbow.com',
    'float_field': 0.443,
    'integer_field': 55,
    'null_boolean_field': True,
    'positive_integer_field': 1,
    'positive_small_integer_field': 1,
    'slug_field': 'slug-friendly-text',
    'small_integer_field': 1,
    'text_field': 'lorem ipsum',
    'time_field': str(datetime.now().time()),
    'url_field': 'https://overtherainbow.com'
}

data_list = [data for _ in range(100)]


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegularFieldsModel2
        fields = list(data.keys()) + ['method']


class TestNestedSerializer(serializers.ModelSerializer):
    fk = TestSerializer()

    class Meta:
        model = RegularFieldsAndFKModel2
        fields = list(data.keys()) + ['fk', 'method']

    def create(self, validated_data):
        fk = RegularFieldsModel2.objects.create(**validated_data['fk'])
        validated_data['fk'] = fk

        return RegularFieldsAndFKModel2.objects.create(**validated_data)

    def update(self, instance, validated_data):
        fk_data = validated_data.pop('fk')
        fk_pk = fk_data.pop('auto_field', None)

        if not fk_pk:
            fk_pk = instance.fk_id

        RegularFieldsModel2.objects.filter(pk=fk_pk).update(**fk_data)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.fk_id = fk_pk
        instance.save()

        return instance


class RegularFieldsAndFKViewSet(viewsets.ModelViewSet):
    queryset = RegularFieldsAndFKModel2.objects.all()
    serializer_class = TestNestedSerializer


class FilteredRegularFieldsAndFKViewSet(RegularFieldsAndFKViewSet):
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('big_integer_field',)


router = DefaultRouter()
router.register('benchmark', RegularFieldsAndFKViewSet, base_name='benchmark')
router.register('benchmark2', FilteredRegularFieldsAndFKViewSet, base_name='benchmark-filter')

urlpatterns = router.urls


class FullStackBenchmarksTestCase(APITransactionTestCase):
    urls = 'tests.test_full_stack_benchmarks'

    def setUp(self):
        RegularFieldsModel2.objects.bulk_create([RegularFieldsModel2(**d) for d in data_list])

        RegularFieldsAndFKModel2.objects.bulk_create(
            [RegularFieldsAndFKModel2(fk=o, **data) for o in RegularFieldsModel2.objects.all()])

        self.first_pk = RegularFieldsAndFKModel2.objects.only('pk').first().pk
        self.last_pk = RegularFieldsAndFKModel2.objects.only('pk').last().pk

    @mark.bench('viewsets.ModelViewSet.list', iterations=1000)
    def test_viewset_list(self):
        url = reverse('benchmark-list')

        response = self.client.get(url)
        assert response.status_code == 200, (response.rendered_content, url)

    @mark.bench('viewsets.ModelViewSet.retrieve', iterations=10000)
    def test_viewset_retrieve(self):
        url = reverse('benchmark-detail', args=[self.first_pk])

        response = self.client.get(url)
        assert response.status_code == 200, (response.rendered_content, url)

    @mark.bench('viewsets.ModelViewSet.create', iterations=1000)
    def test_viewset_create(self):
        url = reverse('benchmark-list')

        new_data = data.copy()
        new_data['fk'] = data.copy()

        response = self.client.post(url, data=new_data, format='json')
        assert response.status_code == 201, (response.rendered_content, url)

    @mark.bench('viewsets.ModelViewSet.update', iterations=1000)
    def test_viewset_update(self):
        url = reverse('benchmark-detail', args=[self.first_pk])

        new_data = data.copy()
        new_fk = RegularFieldsModel2.objects.create(**data)
        new_fk_data = data.copy()
        new_fk_data['auto_field'] = new_fk.pk
        new_data['fk'] = new_fk_data

        response = self.client.put(url, data=new_data, format='json')
        assert response.status_code == 200, (response.rendered_content, url)

    @mark.bench('viewsets.ModelViewSet.partial_update', iterations=1000)
    def test_viewset_partial_update(self):
        url = reverse('benchmark-detail', args=[self.first_pk])

        new_fk = RegularFieldsModel2.objects.create(**data)
        new_fk_data = data.copy()
        new_fk_data['auto_field'] = new_fk.pk
        new_data = {'fk': new_fk_data}

        response = self.client.patch(url, data=new_data)
        assert response.status_code == 200, (response.rendered_content, url)

    @mark.bench('viewsets.ModelViewSet.destroy', iterations=10000)
    def test_viewset_delete(self):
        new_fk = RegularFieldsModel2.objects.create(**data)
        new_obj = RegularFieldsAndFKModel2.objects.create(fk=new_fk, **data)

        url = reverse('benchmark-detail', args=[new_obj.pk])

        response = self.client.delete(url)
        assert response.status_code == 204, (response.rendered_content, url)


class FullStackFilteredBenchmarksTestCase(APITransactionTestCase):
    urls = 'tests.test_full_stack_benchmarks'

    def setUp(self):
        RegularFieldsModel2.objects.bulk_create([RegularFieldsModel2(**d) for d in data_list])

        RegularFieldsAndFKModel2.objects.bulk_create(
            [RegularFieldsAndFKModel2(fk=o, **data) for o in RegularFieldsModel2.objects.all()])

        self.first_pk = RegularFieldsAndFKModel2.objects.only('pk').first().pk
        self.last_pk = RegularFieldsAndFKModel2.objects.only('pk').last().pk

    @mark.bench('viewsets.ModelViewSet.list', iterations=1000)
    def test_viewset_list(self):
        url = reverse('benchmark-filter-list')

        response = self.client.get(url, data={'big_integer_field': 100000})
        assert response.status_code == 200, (response.rendered_content, url)

    @mark.bench('viewsets.ModelViewSet.retrieve', iterations=10000)
    def test_viewset_retrieve(self):
        url = reverse('benchmark-filter-detail', args=[self.first_pk])

        response = self.client.get(url, data={'big_integer_field': 100000})
        assert response.status_code == 200, (response.rendered_content, url)

    @mark.bench('viewsets.ModelViewSet.list', iterations=1000)
    def test_viewset_list_nothing(self):
        url = reverse('benchmark-filter-list')

        response = self.client.get(url, data={'big_integer_field': 100001})
        assert response.rendered_content == '[]', (response.rendered_content, url)

    @mark.bench('viewsets.ModelViewSet.retrieve', iterations=10000)
    @unittest.skip('pytest-bench cannot benchmark operations that raise exceptions')
    def test_viewset_retrieve_nothing(self):
        url = reverse('benchmark-filter-detail', args=[self.first_pk])

        response = self.client.get(url, data={'big_integer_field': 100001})
        assert response.status_code == 404, (response.rendered_content, url)
