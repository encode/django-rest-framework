"""
General tests for relational fields.
"""

from django.db import models
from django.test import TestCase
from rest_framework import serializers


class TimestampedModel(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class TimestampedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimestampedModel


class ReadOnlyFieldTests(TestCase):
    def test_auto_now_fields_read_only(self):
        """
        auto_now and auto_now_add fields should be readonly by default.
        """
        serializer = TimestampedModelSerializer()
        self.assertEquals(serializer.fields['added'].read_only, True)
