"""
General serializer field tests.
"""
from __future__ import unicode_literals
import datetime
from django.db import models
from django.test import TestCase
from django.core import validators
from rest_framework import serializers


class TimestampedModel(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class CharPrimaryKeyModel(models.Model):
    id = models.CharField(max_length=20, primary_key=True)


class TimestampedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimestampedModel


class CharPrimaryKeyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharPrimaryKeyModel


class TimeFieldModel(models.Model):
    clock = models.TimeField()


class TimeFieldModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeFieldModel


class BasicFieldTests(TestCase):
    def test_auto_now_fields_read_only(self):
        """
        auto_now and auto_now_add fields should be read_only by default.
        """
        serializer = TimestampedModelSerializer()
        self.assertEquals(serializer.fields['added'].read_only, True)

    def test_auto_pk_fields_read_only(self):
        """
        AutoField fields should be read_only by default.
        """
        serializer = TimestampedModelSerializer()
        self.assertEquals(serializer.fields['id'].read_only, True)

    def test_non_auto_pk_fields_not_read_only(self):
        """
        PK fields other than AutoField fields should not be read_only by default.
        """
        serializer = CharPrimaryKeyModelSerializer()
        self.assertEquals(serializer.fields['id'].read_only, False)

    def test_TimeField_from_native(self):
        f = serializers.TimeField()
        result = f.from_native('12:34:56.987654')

        self.assertEqual(datetime.time(12, 34, 56, 987654), result)

    def test_TimeField_from_native_datetime_time(self):
        """
        Make sure from_native() accepts a datetime.time instance.
        """
        f = serializers.TimeField()
        result = f.from_native(datetime.time(12, 34, 56))
        self.assertEqual(result, datetime.time(12, 34, 56))

    def test_TimeField_from_native_empty(self):
        f = serializers.TimeField()
        result = f.from_native('')
        self.assertEqual(result, None)

    def test_TimeField_from_native_invalid_time(self):
        f = serializers.TimeField()

        try:
            f.from_native('12:69:12')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["'12:69:12' value has an invalid "
                                          "format. It must be a valid time "
                                          "in the HH:MM[:ss[.uuuuuu]] format."])
        else:
            self.fail("ValidationError was not properly raised")

    def test_TimeFieldModelSerializer(self):
        serializer = TimeFieldModelSerializer()
        self.assertTrue(isinstance(serializer.fields['clock'], serializers.TimeField))
