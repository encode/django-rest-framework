"""
General tests for relational fields.
"""

from django.db import models
from django.test import TestCase
from rest_framework import serializers


class NullModel(models.Model):
    pass


class FieldTests(TestCase):
    def test_pk_related_field_with_empty_string(self):
        """
        Regression test for #446

        https://github.com/tomchristie/django-rest-framework/issues/446
        """
        field = serializers.PrimaryKeyRelatedField(queryset=NullModel.objects.all())
        self.assertRaises(serializers.ValidationError, field.from_native, '')
        self.assertRaises(serializers.ValidationError, field.from_native, [])

    def test_hyperlinked_related_field_with_empty_string(self):
        field = serializers.HyperlinkedRelatedField(queryset=NullModel.objects.all(), view_name='')
        self.assertRaises(serializers.ValidationError, field.from_native, '')
        self.assertRaises(serializers.ValidationError, field.from_native, [])

    def test_slug_related_field_with_empty_string(self):
        field = serializers.SlugRelatedField(queryset=NullModel.objects.all(), slug_field='pk')
        self.assertRaises(serializers.ValidationError, field.from_native, '')
        self.assertRaises(serializers.ValidationError, field.from_native, [])
