"""
General serializer field tests.
"""
from __future__ import unicode_literals

import datetime
import re
from decimal import Decimal
from uuid import uuid4
from django.core import validators
from django.db import models
from django.test import TestCase
from django.utils.datastructures import SortedDict
from rest_framework import serializers
from rest_framework.tests.models import RESTFrameworkModel


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


SAMPLE_CHOICES = [
    ('red', 'Red'),
    ('green', 'Green'),
    ('blue', 'Blue'),
]


class ChoiceFieldModel(models.Model):
    choice = models.CharField(choices=SAMPLE_CHOICES, blank=True, max_length=255)


class ChoiceFieldModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChoiceFieldModel


class ChoiceFieldModelWithNull(models.Model):
    choice = models.CharField(choices=SAMPLE_CHOICES, blank=True, null=True, max_length=255)


class ChoiceFieldModelWithNullSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChoiceFieldModelWithNull


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

    def test_widget_html_attributes(self):
        """
        Make sure widget_html() renders the correct attributes
        """
        r = re.compile('(\S+)=["\']?((?:.(?!["\']?\s+(?:\S+)=|[>"\']))+.)["\']?')
        form = TimeFieldModelSerializer().data
        attributes = r.findall(form.fields['clock'].widget_html())
        self.assertIn(('name', 'clock'), attributes)
        self.assertIn(('id', 'clock'), attributes)


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
                                          "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]"])
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
                                          "YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]"])
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
        class DecimalSerializer(serializers.Serializer):
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
        class DecimalSerializer(serializers.Serializer):
            decimal_field = serializers.DecimalField(max_value=100)

        s = DecimalSerializer(data={'decimal_field': '123'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure this value is less than or equal to 100.']})

    def test_raise_min_value(self):
        """
        Make sure min_value violations raises ValidationError
        """
        class DecimalSerializer(serializers.Serializer):
            decimal_field = serializers.DecimalField(min_value=100)

        s = DecimalSerializer(data={'decimal_field': '99'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure this value is greater than or equal to 100.']})

    def test_raise_max_digits(self):
        """
        Make sure max_digits violations raises ValidationError
        """
        class DecimalSerializer(serializers.Serializer):
            decimal_field = serializers.DecimalField(max_digits=5)

        s = DecimalSerializer(data={'decimal_field': '123.456'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure that there are no more than 5 digits in total.']})

    def test_raise_max_decimal_places(self):
        """
        Make sure max_decimal_places violations raises ValidationError
        """
        class DecimalSerializer(serializers.Serializer):
            decimal_field = serializers.DecimalField(decimal_places=3)

        s = DecimalSerializer(data={'decimal_field': '123.4567'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure that there are no more than 3 decimal places.']})

    def test_raise_max_whole_digits(self):
        """
        Make sure max_whole_digits violations raises ValidationError
        """
        class DecimalSerializer(serializers.Serializer):
            decimal_field = serializers.DecimalField(max_digits=4, decimal_places=3)

        s = DecimalSerializer(data={'decimal_field': '12345.6'})

        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'decimal_field': ['Ensure that there are no more than 4 digits in total.']})


class ChoiceFieldTests(TestCase):
    """
    Tests for the ChoiceField options generator
    """
    def test_choices_required(self):
        """
        Make sure proper choices are rendered if field is required
        """
        f = serializers.ChoiceField(required=True, choices=SAMPLE_CHOICES)
        self.assertEqual(f.choices, SAMPLE_CHOICES)

    def test_choices_not_required(self):
        """
        Make sure proper choices (plus blank) are rendered if the field isn't required
        """
        f = serializers.ChoiceField(required=False, choices=SAMPLE_CHOICES)
        self.assertEqual(f.choices, models.fields.BLANK_CHOICE_DASH + SAMPLE_CHOICES)

    def test_blank_choice_display(self):
        blank = 'No Preference'
        f = serializers.ChoiceField(
            required=False,
            choices=SAMPLE_CHOICES,
            blank_display_value=blank,
        )
        self.assertEqual(f.choices, [('', blank)] + SAMPLE_CHOICES)

    def test_invalid_choice_model(self):
        s = ChoiceFieldModelSerializer(data={'choice': 'wrong_value'})
        self.assertFalse(s.is_valid())
        self.assertEqual(s.errors,  {'choice': ['Select a valid choice. wrong_value is not one of the available choices.']})
        self.assertEqual(s.data['choice'], '')

    def test_empty_choice_model(self):
        """
        Test that the 'empty' value is correctly passed and used depending on
        the 'null' property on the model field.
        """
        s = ChoiceFieldModelSerializer(data={'choice': ''})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.data['choice'], '')

        s = ChoiceFieldModelWithNullSerializer(data={'choice': ''})
        self.assertTrue(s.is_valid())
        self.assertEqual(s.data['choice'], None)

    def test_from_native_empty(self):
        """
        Make sure from_native() returns an empty string on empty param by default.
        """
        f = serializers.ChoiceField(choices=SAMPLE_CHOICES)
        self.assertEqual(f.from_native(''), '')
        self.assertEqual(f.from_native(None), '')

    def test_from_native_empty_override(self):
        """
        Make sure you can override from_native() behavior regarding empty values.
        """
        f = serializers.ChoiceField(choices=SAMPLE_CHOICES, empty=None)
        self.assertEqual(f.from_native(''), None)
        self.assertEqual(f.from_native(None), None)

    def test_metadata_choices(self):
        """
        Make sure proper choices are included in the field's metadata.
        """
        choices = [{'value': v, 'display_name': n} for v, n in SAMPLE_CHOICES]
        f = serializers.ChoiceField(choices=SAMPLE_CHOICES)
        self.assertEqual(f.metadata()['choices'], choices)

    def test_metadata_choices_not_required(self):
        """
        Make sure proper choices are included in the field's metadata.
        """
        choices = [{'value': v, 'display_name': n}
                   for v, n in models.fields.BLANK_CHOICE_DASH + SAMPLE_CHOICES]
        f = serializers.ChoiceField(required=False, choices=SAMPLE_CHOICES)
        self.assertEqual(f.metadata()['choices'], choices)


class EmailFieldTests(TestCase):
    """
    Tests for EmailField attribute values
    """

    class EmailFieldModel(RESTFrameworkModel):
        email_field = models.EmailField(blank=True)

    class EmailFieldWithGivenMaxLengthModel(RESTFrameworkModel):
        email_field = models.EmailField(max_length=150, blank=True)

    def test_default_model_value(self):
        class EmailFieldSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.EmailFieldModel

        serializer = EmailFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['email_field'], 'max_length'), 75)

    def test_given_model_value(self):
        class EmailFieldSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.EmailFieldWithGivenMaxLengthModel

        serializer = EmailFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['email_field'], 'max_length'), 150)

    def test_given_serializer_value(self):
        class EmailFieldSerializer(serializers.ModelSerializer):
            email_field = serializers.EmailField(source='email_field', max_length=20, required=False)

            class Meta:
                model = self.EmailFieldModel

        serializer = EmailFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['email_field'], 'max_length'), 20)


class SlugFieldTests(TestCase):
    """
    Tests for SlugField attribute values
    """

    class SlugFieldModel(RESTFrameworkModel):
        slug_field = models.SlugField(blank=True)

    class SlugFieldWithGivenMaxLengthModel(RESTFrameworkModel):
        slug_field = models.SlugField(max_length=84, blank=True)

    def test_default_model_value(self):
        class SlugFieldSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.SlugFieldModel

        serializer = SlugFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['slug_field'], 'max_length'), 50)

    def test_given_model_value(self):
        class SlugFieldSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.SlugFieldWithGivenMaxLengthModel

        serializer = SlugFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['slug_field'], 'max_length'), 84)

    def test_given_serializer_value(self):
        class SlugFieldSerializer(serializers.ModelSerializer):
            slug_field = serializers.SlugField(source='slug_field',
                                               max_length=20, required=False)

            class Meta:
                model = self.SlugFieldModel

        serializer = SlugFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['slug_field'],
                                 'max_length'), 20)

    def test_invalid_slug(self):
        """
        Make sure an invalid slug raises ValidationError
        """
        class SlugFieldSerializer(serializers.ModelSerializer):
            slug_field = serializers.SlugField(source='slug_field', max_length=20, required=True)

            class Meta:
                model = self.SlugFieldModel

        s = SlugFieldSerializer(data={'slug_field': 'a b'})

        self.assertEqual(s.is_valid(), False)
        self.assertEqual(s.errors,  {'slug_field': ["Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens."]})


class URLFieldTests(TestCase):
    """
    Tests for URLField attribute values.

    (Includes test for #1210, checking that validators can be overridden.)
    """

    class URLFieldModel(RESTFrameworkModel):
        url_field = models.URLField(blank=True)

    class URLFieldWithGivenMaxLengthModel(RESTFrameworkModel):
        url_field = models.URLField(max_length=128, blank=True)

    def test_default_model_value(self):
        class URLFieldSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.URLFieldModel

        serializer = URLFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['url_field'],
                                 'max_length'), 200)

    def test_given_model_value(self):
        class URLFieldSerializer(serializers.ModelSerializer):
            class Meta:
                model = self.URLFieldWithGivenMaxLengthModel

        serializer = URLFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['url_field'],
                                 'max_length'), 128)

    def test_given_serializer_value(self):
        class URLFieldSerializer(serializers.ModelSerializer):
            url_field = serializers.URLField(source='url_field',
                                             max_length=20, required=False)

            class Meta:
                model = self.URLFieldWithGivenMaxLengthModel

        serializer = URLFieldSerializer(data={})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(getattr(serializer.fields['url_field'],
                         'max_length'), 20)

    def test_validators_can_be_overridden(self):
        url_field = serializers.URLField(validators=[])
        validators = url_field.validators
        self.assertEqual([], validators, 'Passing `validators` kwarg should have overridden default validators')


class FieldMetadata(TestCase):
    def setUp(self):
        self.required_field = serializers.Field()
        self.required_field.label = uuid4().hex
        self.required_field.required = True

        self.optional_field = serializers.Field()
        self.optional_field.label = uuid4().hex
        self.optional_field.required = False

    def test_required(self):
        self.assertEqual(self.required_field.metadata()['required'], True)

    def test_optional(self):
        self.assertEqual(self.optional_field.metadata()['required'], False)

    def test_label(self):
        for field in (self.required_field, self.optional_field):
            self.assertEqual(field.metadata()['label'], field.label)


class FieldCallableDefault(TestCase):
    def setUp(self):
        self.simple_callable = lambda: 'foo bar'

    def test_default_can_be_simple_callable(self):
        """
        Ensure that the 'default' argument can also be a simple callable.
        """
        field = serializers.WritableField(default=self.simple_callable)
        into = {}
        field.field_from_native({}, {}, 'field', into)
        self.assertEqual(into, {'field': 'foo bar'})


class CustomIntegerField(TestCase):
    """
        Test that custom fields apply min_value and max_value constraints
    """
    def test_custom_fields_can_be_validated_for_value(self):

        class MoneyField(models.PositiveIntegerField):
            pass

        class EntryModel(models.Model):
            bank = MoneyField(validators=[validators.MaxValueValidator(100)])

        class EntrySerializer(serializers.ModelSerializer):
            class Meta:
                model = EntryModel

        entry = EntryModel(bank=1)

        serializer = EntrySerializer(entry, data={"bank": 11})
        self.assertTrue(serializer.is_valid())

        serializer = EntrySerializer(entry, data={"bank": -1})
        self.assertFalse(serializer.is_valid())

        serializer = EntrySerializer(entry, data={"bank": 101})
        self.assertFalse(serializer.is_valid())


class BooleanField(TestCase):
    """
        Tests for BooleanField
    """
    def test_boolean_required(self):
        class BooleanRequiredSerializer(serializers.Serializer):
            bool_field = serializers.BooleanField(required=True)

        self.assertFalse(BooleanRequiredSerializer(data={}).is_valid())
