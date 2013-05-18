"""
General serializer field tests.
"""
from __future__ import unicode_literals
from django.utils.datastructures import SortedDict
import datetime
from decimal import Decimal
from django.db import models
from django.test import TestCase
from django.core import validators
from rest_framework import serializers
from rest_framework.serializers import Serializer


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
        self.assertEqual(serializer.fields['added'].read_only, True)

    def test_auto_pk_fields_read_only(self):
        """
        AutoField fields should be read_only by default.
        """
        serializer = TimestampedModelSerializer()
        self.assertEqual(serializer.fields['id'].read_only, True)

    def test_non_auto_pk_fields_not_read_only(self):
        """
        PK fields other than AutoField fields should not be read_only by default.
        """
        serializer = CharPrimaryKeyModelSerializer()
        self.assertEqual(serializer.fields['id'].read_only, False)

    def test_dict_field_ordering(self):
        """
        Field should preserve dictionary ordering, if it exists.
        See: https://github.com/tomchristie/django-rest-framework/issues/832
        """
        ret = SortedDict()
        ret['c'] = 1
        ret['b'] = 1
        ret['a'] = 1
        ret['z'] = 1
        field = serializers.Field()
        keys = list(field.to_native(ret).keys())
        self.assertEqual(keys, ['c', 'b', 'a', 'z'])


class DateFieldTest(TestCase):
    """
    Tests for the DateFieldTest from_native() and to_native() behavior
    """

    def test_from_native_string(self):
        """
        Make sure from_native() accepts default iso input formats.
        """
        f = serializers.DateField()
        result_1 = f.from_native('1984-07-31')

        self.assertEqual(datetime.date(1984, 7, 31), result_1)

    def test_from_native_datetime_date(self):
        """
        Make sure from_native() accepts a datetime.date instance.
        """
        f = serializers.DateField()
        result_1 = f.from_native(datetime.date(1984, 7, 31))

        self.assertEqual(result_1, datetime.date(1984, 7, 31))

    def test_from_native_custom_format(self):
        """
        Make sure from_native() accepts custom input formats.
        """
        f = serializers.DateField(input_formats=['%Y -- %d'])
        result = f.from_native('1984 -- 31')

        self.assertEqual(datetime.date(1984, 1, 31), result)

    def test_from_native_invalid_default_on_custom_format(self):
        """
        Make sure from_native() don't accept default formats if custom format is preset
        """
        f = serializers.DateField(input_formats=['%Y -- %d'])

        try:
            f.from_native('1984-07-31')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Date has wrong format. Use one of these formats instead: YYYY -- DD"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_from_native_empty(self):
        """
        Make sure from_native() returns None on empty param.
        """
        f = serializers.DateField()
        result = f.from_native('')

        self.assertEqual(result, None)

    def test_from_native_none(self):
        """
        Make sure from_native() returns None on None param.
        """
        f = serializers.DateField()
        result = f.from_native(None)

        self.assertEqual(result, None)

    def test_from_native_invalid_date(self):
        """
        Make sure from_native() raises a ValidationError on passing an invalid date.
        """
        f = serializers.DateField()

        try:
            f.from_native('1984-13-31')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Date has wrong format. Use one of these formats instead: YYYY[-MM[-DD]]"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_from_native_invalid_format(self):
        """
        Make sure from_native() raises a ValidationError on passing an invalid format.
        """
        f = serializers.DateField()

        try:
            f.from_native('1984 -- 31')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Date has wrong format. Use one of these formats instead: YYYY[-MM[-DD]]"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_to_native(self):
        """
        Make sure to_native() returns datetime as default.
        """
        f = serializers.DateField()

        result_1 = f.to_native(datetime.date(1984, 7, 31))

        self.assertEqual(datetime.date(1984, 7, 31), result_1)

    def test_to_native_iso(self):
        """
        Make sure to_native() with 'iso-8601' returns iso formated date.
        """
        f = serializers.DateField(format='iso-8601')

        result_1 = f.to_native(datetime.date(1984, 7, 31))

        self.assertEqual('1984-07-31', result_1)

    def test_to_native_custom_format(self):
        """
        Make sure to_native() returns correct custom format.
        """
        f = serializers.DateField(format="%Y - %m.%d")

        result_1 = f.to_native(datetime.date(1984, 7, 31))

        self.assertEqual('1984 - 07.31', result_1)

    def test_to_native_none(self):
        """
        Make sure from_native() returns None on None param.
        """
        f = serializers.DateField(required=False)
        self.assertEqual(None, f.to_native(None))


class DateTimeFieldTest(TestCase):
    """
    Tests for the DateTimeField from_native() and to_native() behavior
    """

    def test_from_native_string(self):
        """
        Make sure from_native() accepts default iso input formats.
        """
        f = serializers.DateTimeField()
        result_1 = f.from_native('1984-07-31 04:31')
        result_2 = f.from_native('1984-07-31 04:31:59')
        result_3 = f.from_native('1984-07-31 04:31:59.000200')

        self.assertEqual(datetime.datetime(1984, 7, 31, 4, 31), result_1)
        self.assertEqual(datetime.datetime(1984, 7, 31, 4, 31, 59), result_2)
        self.assertEqual(datetime.datetime(1984, 7, 31, 4, 31, 59, 200), result_3)

    def test_from_native_datetime_datetime(self):
        """
        Make sure from_native() accepts a datetime.datetime instance.
        """
        f = serializers.DateTimeField()
        result_1 = f.from_native(datetime.datetime(1984, 7, 31, 4, 31))
        result_2 = f.from_native(datetime.datetime(1984, 7, 31, 4, 31, 59))
        result_3 = f.from_native(datetime.datetime(1984, 7, 31, 4, 31, 59, 200))

        self.assertEqual(result_1, datetime.datetime(1984, 7, 31, 4, 31))
        self.assertEqual(result_2, datetime.datetime(1984, 7, 31, 4, 31, 59))
        self.assertEqual(result_3, datetime.datetime(1984, 7, 31, 4, 31, 59, 200))

    def test_from_native_custom_format(self):
        """
        Make sure from_native() accepts custom input formats.
        """
        f = serializers.DateTimeField(input_formats=['%Y -- %H:%M'])
        result = f.from_native('1984 -- 04:59')

        self.assertEqual(datetime.datetime(1984, 1, 1, 4, 59), result)

    def test_from_native_invalid_default_on_custom_format(self):
        """
        Make sure from_native() don't accept default formats if custom format is preset
        """
        f = serializers.DateTimeField(input_formats=['%Y -- %H:%M'])

        try:
            f.from_native('1984-07-31 04:31:59')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Datetime has wrong format. Use one of these formats instead: YYYY -- hh:mm"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_from_native_empty(self):
        """
        Make sure from_native() returns None on empty param.
        """
        f = serializers.DateTimeField()
        result = f.from_native('')

        self.assertEqual(result, None)

    def test_from_native_none(self):
        """
        Make sure from_native() returns None on None param.
        """
        f = serializers.DateTimeField()
        result = f.from_native(None)

        self.assertEqual(result, None)

    def test_from_native_invalid_datetime(self):
        """
        Make sure from_native() raises a ValidationError on passing an invalid datetime.
        """
        f = serializers.DateTimeField()

        try:
            f.from_native('04:61:59')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Datetime has wrong format. Use one of these formats instead: "
                                          "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HHMM|-HHMM|Z]"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_from_native_invalid_format(self):
        """
        Make sure from_native() raises a ValidationError on passing an invalid format.
        """
        f = serializers.DateTimeField()

        try:
            f.from_native('04 -- 31')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Datetime has wrong format. Use one of these formats instead: "
                                          "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HHMM|-HHMM|Z]"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_to_native(self):
        """
        Make sure to_native() returns isoformat as default.
        """
        f = serializers.DateTimeField()

        result_1 = f.to_native(datetime.datetime(1984, 7, 31))
        result_2 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31))
        result_3 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31, 59))
        result_4 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31, 59, 200))

        self.assertEqual(datetime.datetime(1984, 7, 31), result_1)
        self.assertEqual(datetime.datetime(1984, 7, 31, 4, 31), result_2)
        self.assertEqual(datetime.datetime(1984, 7, 31, 4, 31, 59), result_3)
        self.assertEqual(datetime.datetime(1984, 7, 31, 4, 31, 59, 200), result_4)

    def test_to_native_iso(self):
        """
        Make sure to_native() with format=iso-8601 returns iso formatted datetime.
        """
        f = serializers.DateTimeField(format='iso-8601')

        result_1 = f.to_native(datetime.datetime(1984, 7, 31))
        result_2 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31))
        result_3 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31, 59))
        result_4 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31, 59, 200))

        self.assertEqual('1984-07-31T00:00:00', result_1)
        self.assertEqual('1984-07-31T04:31:00', result_2)
        self.assertEqual('1984-07-31T04:31:59', result_3)
        self.assertEqual('1984-07-31T04:31:59.000200', result_4)

    def test_to_native_custom_format(self):
        """
        Make sure to_native() returns correct custom format.
        """
        f = serializers.DateTimeField(format="%Y - %H:%M")

        result_1 = f.to_native(datetime.datetime(1984, 7, 31))
        result_2 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31))
        result_3 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31, 59))
        result_4 = f.to_native(datetime.datetime(1984, 7, 31, 4, 31, 59, 200))

        self.assertEqual('1984 - 00:00', result_1)
        self.assertEqual('1984 - 04:31', result_2)
        self.assertEqual('1984 - 04:31', result_3)
        self.assertEqual('1984 - 04:31', result_4)

    def test_to_native_none(self):
        """
        Make sure from_native() returns None on None param.
        """
        f = serializers.DateTimeField(required=False)
        self.assertEqual(None, f.to_native(None))


class TimeFieldTest(TestCase):
    """
    Tests for the TimeField from_native() and to_native() behavior
    """

    def test_from_native_string(self):
        """
        Make sure from_native() accepts default iso input formats.
        """
        f = serializers.TimeField()
        result_1 = f.from_native('04:31')
        result_2 = f.from_native('04:31:59')
        result_3 = f.from_native('04:31:59.000200')

        self.assertEqual(datetime.time(4, 31), result_1)
        self.assertEqual(datetime.time(4, 31, 59), result_2)
        self.assertEqual(datetime.time(4, 31, 59, 200), result_3)

    def test_from_native_datetime_time(self):
        """
        Make sure from_native() accepts a datetime.time instance.
        """
        f = serializers.TimeField()
        result_1 = f.from_native(datetime.time(4, 31))
        result_2 = f.from_native(datetime.time(4, 31, 59))
        result_3 = f.from_native(datetime.time(4, 31, 59, 200))

        self.assertEqual(result_1, datetime.time(4, 31))
        self.assertEqual(result_2, datetime.time(4, 31, 59))
        self.assertEqual(result_3, datetime.time(4, 31, 59, 200))

    def test_from_native_custom_format(self):
        """
        Make sure from_native() accepts custom input formats.
        """
        f = serializers.TimeField(input_formats=['%H -- %M'])
        result = f.from_native('04 -- 31')

        self.assertEqual(datetime.time(4, 31), result)

    def test_from_native_invalid_default_on_custom_format(self):
        """
        Make sure from_native() don't accept default formats if custom format is preset
        """
        f = serializers.TimeField(input_formats=['%H -- %M'])

        try:
            f.from_native('04:31:59')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Time has wrong format. Use one of these formats instead: hh -- mm"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_from_native_empty(self):
        """
        Make sure from_native() returns None on empty param.
        """
        f = serializers.TimeField()
        result = f.from_native('')

        self.assertEqual(result, None)

    def test_from_native_none(self):
        """
        Make sure from_native() returns None on None param.
        """
        f = serializers.TimeField()
        result = f.from_native(None)

        self.assertEqual(result, None)

    def test_from_native_invalid_time(self):
        """
        Make sure from_native() raises a ValidationError on passing an invalid time.
        """
        f = serializers.TimeField()

        try:
            f.from_native('04:61:59')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Time has wrong format. Use one of these formats instead: "
                                          "hh:mm[:ss[.uuuuuu]]"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_from_native_invalid_format(self):
        """
        Make sure from_native() raises a ValidationError on passing an invalid format.
        """
        f = serializers.TimeField()

        try:
            f.from_native('04 -- 31')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Time has wrong format. Use one of these formats instead: "
                                          "hh:mm[:ss[.uuuuuu]]"])
        else:
            self.fail("ValidationError was not properly raised")

    def test_to_native(self):
        """
        Make sure to_native() returns time object as default.
        """
        f = serializers.TimeField()
        result_1 = f.to_native(datetime.time(4, 31))
        result_2 = f.to_native(datetime.time(4, 31, 59))
        result_3 = f.to_native(datetime.time(4, 31, 59, 200))

        self.assertEqual(datetime.time(4, 31), result_1)
        self.assertEqual(datetime.time(4, 31, 59), result_2)
        self.assertEqual(datetime.time(4, 31, 59, 200), result_3)

    def test_to_native_iso(self):
        """
        Make sure to_native() with format='iso-8601' returns iso formatted time.
        """
        f = serializers.TimeField(format='iso-8601')
        result_1 = f.to_native(datetime.time(4, 31))
        result_2 = f.to_native(datetime.time(4, 31, 59))
        result_3 = f.to_native(datetime.time(4, 31, 59, 200))

        self.assertEqual('04:31:00', result_1)
        self.assertEqual('04:31:59', result_2)
        self.assertEqual('04:31:59.000200', result_3)

    def test_to_native_custom_format(self):
        """
        Make sure to_native() returns correct custom format.
        """
        f = serializers.TimeField(format="%H - %S [%f]")
        result_1 = f.to_native(datetime.time(4, 31))
        result_2 = f.to_native(datetime.time(4, 31, 59))
        result_3 = f.to_native(datetime.time(4, 31, 59, 200))

        self.assertEqual('04 - 00 [000000]', result_1)
        self.assertEqual('04 - 59 [000000]', result_2)
        self.assertEqual('04 - 59 [000200]', result_3)


class DecimalFieldTest(TestCase):
    """
    Tests for the DecimalField from_native() and to_native() behavior
    """

    def test_from_native_string(self):
        """
        Make sure from_native() accepts string values
        """
        f = serializers.DecimalField()
        result_1 = f.from_native('9000')
        result_2 = f.from_native('1.00000001')

        self.assertEqual(Decimal('9000'), result_1)
        self.assertEqual(Decimal('1.00000001'), result_2)

    def test_from_native_invalid_string(self):
        """
        Make sure from_native() raises ValidationError on passing invalid string
        """
        f = serializers.DecimalField()

        try:
            f.from_native('123.45.6')
        except validators.ValidationError as e:
            self.assertEqual(e.messages, ["Enter a number."])
        else:
            self.fail("ValidationError was not properly raised")

    def test_from_native_integer(self):
        """
        Make sure from_native() accepts integer values
        """
        f = serializers.DecimalField()
        result = f.from_native(9000)

        self.assertEqual(Decimal('9000'), result)

    def test_from_native_float(self):
        """
        Make sure from_native() accepts float values
        """
        f = serializers.DecimalField()
        result = f.from_native(1.00000001)

        self.assertEqual(Decimal('1.00000001'), result)

    def test_from_native_empty(self):
        """
        Make sure from_native() returns None on empty param.
        """
        f = serializers.DecimalField()
        result = f.from_native('')

        self.assertEqual(result, None)

    def test_from_native_none(self):
        """
        Make sure from_native() returns None on None param.
        """
        f = serializers.DecimalField()
        result = f.from_native(None)

        self.assertEqual(result, None)

    def test_to_native(self):
        """
        Make sure to_native() returns Decimal as string.
        """
        f = serializers.DecimalField()

        result_1 = f.to_native(Decimal('9000'))
        result_2 = f.to_native(Decimal('1.00000001'))

        self.assertEqual(Decimal('9000'), result_1)
        self.assertEqual(Decimal('1.00000001'), result_2)

    def test_to_native_none(self):
        """
        Make sure from_native() returns None on None param.
        """
        f = serializers.DecimalField(required=False)
        self.assertEqual(None, f.to_native(None))

    def test_valid_serialization(self):
        """
        Make sure the serializer works correctly
        """
        class DecimalSerializer(Serializer):
            decimal_field = serializers.DecimalField(max_value=9010,
                                                     min_value=9000,
                                                     max_digits=6,
                                                     decimal_places=2)

        self.assertTrue(DecimalSerializer(data={'decimal_field': '9001'}).is_valid())
        self.assertTrue(DecimalSerializer(data={'decimal_field': '9001.2'}).is_valid())
        self.assertTrue(DecimalSerializer(data={'decimal_field': '9001.23'}).is_valid())

        self.assertFalse(DecimalSerializer(data={'decimal_field': '8000'}).is_valid())
        self.assertFalse(DecimalSerializer(data={'decimal_field': '9900'}).is_valid())
        self.assertFalse(DecimalSerializer(data={'decimal_field': '9001.234'}).is_valid())

    def test_raise_max_value(self):
        """
        Make sure max_value violations raises ValidationError
        """
        class DecimalSerializer(Serializer):
            decimal_field = serializers.DecimalField(max_value=100)

        s = DecimalSerializer(data={'decimal_field': '123'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure this value is less than or equal to 100.']})

    def test_raise_min_value(self):
        """
        Make sure min_value violations raises ValidationError
        """
        class DecimalSerializer(Serializer):
            decimal_field = serializers.DecimalField(min_value=100)

        s = DecimalSerializer(data={'decimal_field': '99'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure this value is greater than or equal to 100.']})

    def test_raise_max_digits(self):
        """
        Make sure max_digits violations raises ValidationError
        """
        class DecimalSerializer(Serializer):
            decimal_field = serializers.DecimalField(max_digits=5)

        s = DecimalSerializer(data={'decimal_field': '123.456'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure that there are no more than 5 digits in total.']})

    def test_raise_max_decimal_places(self):
        """
        Make sure max_decimal_places violations raises ValidationError
        """
        class DecimalSerializer(Serializer):
            decimal_field = serializers.DecimalField(decimal_places=3)

        s = DecimalSerializer(data={'decimal_field': '123.4567'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure that there are no more than 3 decimal places.']})

    def test_raise_max_whole_digits(self):
        """
        Make sure max_whole_digits violations raises ValidationError
        """
        class DecimalSerializer(Serializer):
            decimal_field = serializers.DecimalField(max_digits=4, decimal_places=3)

        s = DecimalSerializer(data={'decimal_field': '12345.6'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure that there are no more than 4 digits in total.']})


class ChoiceFieldTests(TestCase):
    """
    Tests for the ChoiceField options generator
    """

    SAMPLE_CHOICES = [
        ('red', 'Red'),
        ('green', 'Green'),
        ('blue', 'Blue'),
    ]

    def test_choices_required(self):
        """
        Make sure proper choices are rendered if field is required
        """
        f = serializers.ChoiceField(required=True, choices=self.SAMPLE_CHOICES)
        self.assertEqual(f.choices, self.SAMPLE_CHOICES)

    def test_choices_not_required(self):
        """
        Make sure proper choices (plus blank) are rendered if the field isn't required
        """
        f = serializers.ChoiceField(required=False, choices=self.SAMPLE_CHOICES)
        self.assertEqual(f.choices, models.fields.BLANK_CHOICE_DASH + self.SAMPLE_CHOICES)
