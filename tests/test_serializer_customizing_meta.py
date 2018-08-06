# coding: utf-8
from __future__ import unicode_literals

from django.db import models
from django.test import TestCase

from rest_framework import serializers


class Product(models.Model):
    name = models.CharField(max_length=10)


class Item(models.Model):
    f1 = models.CharField(max_length=10)
    f2 = models.CharField(max_length=10000)
    user = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='items')


class TestCustomizingMetaOptions(TestCase):
    def test_meta_fields(self):
        class ItemSerializer(serializers.ModelSerializer):
            class Meta:
                model = Item
                fields = '__all__'

        class ProductSerializer(serializers.ModelSerializer):
            items = ItemSerializer(many=True, meta_fields=['f1'])

            class Meta:
                model = Product
                fields = '__all__'

        ShortenProductSerializer = ProductSerializer.meta_fields('id', 'name')

        self.assertEqual(len(ProductSerializer().fields['items'].child.get_fields()), 1)
        self.assertEqual(len(ShortenProductSerializer().get_fields()), 2)

    def test_meta_fields_all(self):
        class ItemSerializer(serializers.ModelSerializer):
            class Meta:
                model = Item
                fields = ['f1']

        serializer = ItemSerializer(meta_fields='__all__')
        self.assertEqual(len(serializer.get_fields()), 4)

    def test_meta_exclude(self):
        class ItemSerializer(serializers.ModelSerializer):
            class Meta:
                model = Item
                fields = '__all__'

        class ProductSerializer(serializers.ModelSerializer):
            items = ItemSerializer(many=True, meta_exclude=['id', 'f2', 'user'])

            class Meta:
                model = Product
                fields = '__all__'

        ShortenProductSerializer = ProductSerializer.meta_exclude('items')

        self.assertEqual(len(ProductSerializer().fields['items'].child.get_fields()), 1)
        self.assertEqual(len(ShortenProductSerializer().get_fields()), 2)

    def test_meta_exclude_from_defined_fields(self):
        class ItemSerializer(serializers.ModelSerializer):
            class Meta:
                model = Item
                fields = ['user', 'f1', 'f2']

        serializer = ItemSerializer(meta_exclude=['f2'])
        self.assertEqual(len(serializer.get_fields()), 2)

    def test_meta_preset(self):
        class ItemSerializer(serializers.ModelSerializer):
            class Meta:
                model = Item
                fields = '__all__'
                presets = {
                    'short': {
                        'fields': ['f1']
                    }
                }

        class ProductSerializer(serializers.ModelSerializer):
            items = ItemSerializer(many=True, meta_preset='short')

            class Meta:
                model = Product
                fields = '__all__'
                presets = {
                    'short': {
                        'fields': ['id', 'name']
                    },
                    'light': {
                        'exclude': ['items']
                    }
                }

        ShortenProductSerializer = ProductSerializer.meta_preset('short')

        self.assertEqual(len(ProductSerializer().fields['items'].child.get_fields()), 1)
        self.assertEqual(len(ShortenProductSerializer().get_fields()), 2)
