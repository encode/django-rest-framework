from decimal import Decimal

from django.test import TestCase, override_settings
from django.utils import six

from rest_framework import serializers

from .base import FieldValues


class TestDecimalField(FieldValues):
    """
    Valid and invalid values for `DecimalField`.
    """
    valid_inputs = {
        '12.3': Decimal('12.3'),
        '0.1': Decimal('0.1'),
        10: Decimal('10'),
        0: Decimal('0'),
        12.3: Decimal('12.3'),
        0.1: Decimal('0.1'),
        '2E+1': Decimal('20'),
    }
    invalid_inputs = (
        ('abc', ["A valid number is required."]),
        (Decimal('Nan'), ["A valid number is required."]),
        (Decimal('Inf'), ["A valid number is required."]),
        ('12.345', ["Ensure that there are no more than 3 digits in total."]),
        (200000000000.0, ["Ensure that there are no more than 3 digits in total."]),
        ('0.01', ["Ensure that there are no more than 1 decimal places."]),
        (123, ["Ensure that there are no more than 2 digits before the decimal point."]),
        ('2E+2', ["Ensure that there are no more than 2 digits before the decimal point."])
    )
    outputs = {
        '1': '1.0',
        '0': '0.0',
        '1.09': '1.1',
        '0.04': '0.0',
        1: '1.0',
        0: '0.0',
        Decimal('1.0'): '1.0',
        Decimal('0.0'): '0.0',
        Decimal('1.09'): '1.1',
        Decimal('0.04'): '0.0'
    }
    field = serializers.DecimalField(max_digits=3, decimal_places=1)


class TestMinMaxDecimalField(FieldValues):
    """
    Valid and invalid values for `DecimalField` with min and max limits.
    """
    valid_inputs = {
        '10.0': Decimal('10.0'),
        '20.0': Decimal('20.0'),
    }
    invalid_inputs = {
        '9.9': ['Ensure this value is greater than or equal to 10.'],
        '20.1': ['Ensure this value is less than or equal to 20.'],
    }
    outputs = {}
    field = serializers.DecimalField(
        max_digits=3, decimal_places=1,
        min_value=10, max_value=20
    )


class TestNoMaxDigitsDecimalField(FieldValues):
    field = serializers.DecimalField(
        max_value=100, min_value=0,
        decimal_places=2, max_digits=None
    )
    valid_inputs = {
        '10': Decimal('10.00')
    }
    invalid_inputs = {}
    outputs = {}


class TestNoStringCoercionDecimalField(FieldValues):
    """
    Output values for `DecimalField` with `coerce_to_string=False`.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        1.09: Decimal('1.1'),
        0.04: Decimal('0.0'),
        '1.09': Decimal('1.1'),
        '0.04': Decimal('0.0'),
        Decimal('1.09'): Decimal('1.1'),
        Decimal('0.04'): Decimal('0.0'),
    }
    field = serializers.DecimalField(
        max_digits=3, decimal_places=1,
        coerce_to_string=False
    )


class TestLocalizedDecimalField(TestCase):
    @override_settings(USE_L10N=True, LANGUAGE_CODE='pl')
    def test_to_internal_value(self):
        field = serializers.DecimalField(max_digits=2, decimal_places=1, localize=True)
        self.assertEqual(field.to_internal_value('1,1'), Decimal('1.1'))

    @override_settings(USE_L10N=True, LANGUAGE_CODE='pl')
    def test_to_representation(self):
        field = serializers.DecimalField(max_digits=2, decimal_places=1, localize=True)
        self.assertEqual(field.to_representation(Decimal('1.1')), '1,1')

    def test_localize_forces_coerce_to_string(self):
        field = serializers.DecimalField(max_digits=2, decimal_places=1, coerce_to_string=False, localize=True)
        self.assertTrue(isinstance(field.to_representation(Decimal('1.1')), six.string_types))


class TestQuantizedValueForDecimal(TestCase):
    def test_int_quantized_value_for_decimal(self):
        field = serializers.DecimalField(max_digits=4, decimal_places=2)
        value = field.to_internal_value(12).as_tuple()
        expected_digit_tuple = (0, (1, 2, 0, 0), -2)
        self.assertEqual(value, expected_digit_tuple)

    def test_string_quantized_value_for_decimal(self):
        field = serializers.DecimalField(max_digits=4, decimal_places=2)
        value = field.to_internal_value('12').as_tuple()
        expected_digit_tuple = (0, (1, 2, 0, 0), -2)
        self.assertEqual(value, expected_digit_tuple)

    def test_part_precision_string_quantized_value_for_decimal(self):
        field = serializers.DecimalField(max_digits=4, decimal_places=2)
        value = field.to_internal_value('12.0').as_tuple()
        expected_digit_tuple = (0, (1, 2, 0, 0), -2)
        self.assertEqual(value, expected_digit_tuple)


class TestNoDecimalPlaces(FieldValues):
    valid_inputs = {
        '0.12345': Decimal('0.12345'),
    }
    invalid_inputs = {
        '0.1234567': ['Ensure that there are no more than 6 digits in total.']
    }
    outputs = {
        '1.2345': '1.2345',
        '0': '0',
        '1.1': '1.1',
    }
    field = serializers.DecimalField(max_digits=6, decimal_places=None)
