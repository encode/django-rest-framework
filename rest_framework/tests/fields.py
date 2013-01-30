"""
General serializer field tests.
"""

import django
from django.db import models
from django.test import TestCase
from django.utils import unittest
from rest_framework import serializers


class TimestampedModel(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class CharPrimaryKeyModel(models.Model):
    id = models.CharField(max_length=20, primary_key=True)


class DateObject(object):
    def __init__(self, date):
        self.date = date


class DateTimeObject(object):
    def __init__(self, date_time):
        self.date_time = date_time


class TimestampedModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimestampedModel


class CharPrimaryKeyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CharPrimaryKeyModel


class DateObjectSerializer(serializers.Serializer):
    date = serializers.DateField()

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.date = attrs['date']
            return instance
        return DateObject(**attrs)


class DateObjectCustomFormatSerializer(serializers.Serializer):
    date = serializers.DateField(format=("%Y", "%Y -- %m"))

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.date = attrs['date']
            return instance
        return DateObject(**attrs)


class DateTimeObjectSerializer(serializers.Serializer):
    date_time = serializers.DateTimeField()

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.date_time = attrs['date_time']
            return instance
        return DateTimeObject(**attrs)


class DateTimeObjectCustomFormatSerializer(serializers.Serializer):
    date_time = serializers.DateTimeField(format=("%Y", "%Y %H:%M"))

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.date_time = attrs['date_time']
            return instance
        return DateTimeObject(**attrs)


class ReadOnlyFieldTests(TestCase):
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


class DateValidationTest(TestCase):
    def test_valid_default_date_input_formats(self):
        serializer = DateObjectSerializer(data={'date': '1984-07-31'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': '07/31/1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': '07/31/84'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': 'Jul 31 1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': 'Jul 31, 1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': '31 Jul 1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': '31 Jul 1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': 'July 31 1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': 'July 31, 1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': '31 July 1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectSerializer(data={'date': '31 July, 1984'})
        self.assertTrue(serializer.is_valid())

    def test_valid_custom_date_input_formats(self):
        serializer = DateObjectCustomFormatSerializer(data={'date': '1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateObjectCustomFormatSerializer(data={'date': '1984 -- 07'})
        self.assertTrue(serializer.is_valid())

    def test_wrong_default_date_input_format(self):
        serializer = DateObjectSerializer(data={'date': 'something wrong'})
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'date': [u'Date has wrong format. Use one of these formats instead: '
                                                       u'YYYY-MM-DD; MM/DD/YYYY; MM/DD/YY; [Jan through Dec] DD YYYY; '
                                                       u'[Jan through Dec] DD, YYYY; DD [Jan through Dec] YYYY; '
                                                       u'DD [Jan through Dec], YYYY; [January through December] DD YYYY; '
                                                       u'[January through December] DD, YYYY; DD [January through December] YYYY; '
                                                       u'DD [January through December], YYYY']})

    def test_wrong_custom_date_input_format(self):
        serializer = DateObjectCustomFormatSerializer(data={'date': '07/31/1984'})
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'date': [u'Date has wrong format. Use one of these formats instead: YYYY; YYYY -- MM']})


class DateTimeValidationTest(TestCase):
    def test_valid_default_date_time_input_formats(self):
        serializer = DateTimeObjectSerializer(data={'date_time': '1984-07-31 04:31:59'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '1984-07-31 04:31'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '1984-07-31'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '07/31/1984 04:31:59'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '07/31/1984 04:31'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '07/31/1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '07/31/84 04:31:59'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '07/31/84 04:31'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '07/31/84'})
        self.assertTrue(serializer.is_valid())

    @unittest.skipUnless(django.VERSION >= (1, 4), "django < 1.4 don't have microseconds in default settings")
    def test_valid_default_date_time_input_formats_for_django_gte_1_4(self):
        serializer = DateTimeObjectSerializer(data={'date_time': '1984-07-31 04:31:59.123456'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '07/31/1984 04:31:59.123456'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectSerializer(data={'date_time': '07/31/84 04:31:59.123456'})
        self.assertTrue(serializer.is_valid())

    def test_valid_custom_date_time_input_formats(self):
        serializer = DateTimeObjectCustomFormatSerializer(data={'date_time': '1984'})
        self.assertTrue(serializer.is_valid())

        serializer = DateTimeObjectCustomFormatSerializer(data={'date_time': '1984 04:31'})
        self.assertTrue(serializer.is_valid())

    @unittest.skipUnless(django.VERSION >= (1, 4), "django < 1.4 don't have microseconds in default settings")
    def test_wrong_default_date_time_input_format_for_django_gte_1_4(self):
        serializer = DateTimeObjectSerializer(data={'date_time': 'something wrong'})
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'date_time': [u'Datetime has wrong format. Use one of these formats instead: '
                                                            u'YYYY-MM-DD HH:MM:SS; YYYY-MM-DD HH:MM:SS.uuuuuu; YYYY-MM-DD HH:MM; '
                                                            u'YYYY-MM-DD; MM/DD/YYYY HH:MM:SS; MM/DD/YYYY HH:MM:SS.uuuuuu; '
                                                            u'MM/DD/YYYY HH:MM; MM/DD/YYYY; MM/DD/YY HH:MM:SS; '
                                                            u'MM/DD/YY HH:MM:SS.uuuuuu; MM/DD/YY HH:MM; MM/DD/YY']})

    @unittest.skipUnless(django.VERSION < (1, 4), "django >= 1.4 have microseconds in default settings")
    def test_wrong_default_date_time_input_format_for_django_lt_1_4(self):
        serializer = DateTimeObjectSerializer(data={'date_time': 'something wrong'})
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'date_time': [u'Datetime has wrong format. Use one of these formats instead:'
                                                            u' YYYY-MM-DD HH:MM:SS; YYYY-MM-DD HH:MM; YYYY-MM-DD; '
                                                            u'MM/DD/YYYY HH:MM:SS; MM/DD/YYYY HH:MM; MM/DD/YYYY; '
                                                            u'MM/DD/YY HH:MM:SS; MM/DD/YY HH:MM; MM/DD/YY']})

    def test_wrong_custom_date_time_input_format(self):
        serializer = DateTimeObjectCustomFormatSerializer(data={'date_time': '07/31/84 04:31'})
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'date_time': [u'Datetime has wrong format. Use one of these formats instead: YYYY; YYYY HH:MM']})
