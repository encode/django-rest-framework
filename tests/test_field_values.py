from decimal import Decimal
from django.utils import timezone
from rest_framework import fields
import datetime
import django
import pytest


def get_items(mapping_or_list_of_two_tuples):
    # Tests accept either lists of two tuples, or dictionaries.
    if isinstance(mapping_or_list_of_two_tuples, dict):
        # {value: expected}
        return mapping_or_list_of_two_tuples.items()
    # [(value, expected), ...]
    return mapping_or_list_of_two_tuples


class FieldValues:
    """
    Base class for testing valid and invalid input values.
    """
    def test_valid_inputs(self):
        """
        Ensure that valid values return the expected validated data.
        """
        for input_value, expected_output in get_items(self.valid_inputs):
            assert self.field.run_validation(input_value) == expected_output

    def test_invalid_inputs(self):
        """
        Ensure that invalid values raise the expected validation error.
        """
        for input_value, expected_failure in get_items(self.invalid_inputs):
            with pytest.raises(fields.ValidationError) as exc_info:
                self.field.run_validation(input_value)
            assert exc_info.value.messages == expected_failure

    def test_outputs(self):
        for output_value, expected_output in get_items(self.outputs):
            assert self.field.to_representation(output_value) == expected_output


# Boolean types...

class TestBooleanField(FieldValues):
    """
    Valid and invalid values for `BooleanField`.
    """
    valid_inputs = {
        'true': True,
        'false': False,
        '1': True,
        '0': False,
        1: True,
        0: False,
        True: True,
        False: False,
    }
    invalid_inputs = {
        'foo': ['`foo` is not a valid boolean.']
    }
    outputs = {
        'true': True,
        'false': False,
        '1': True,
        '0': False,
        1: True,
        0: False,
        True: True,
        False: False,
        'other': True
    }
    field = fields.BooleanField()


# String types...

class TestCharField(FieldValues):
    """
    Valid and invalid values for `CharField`.
    """
    valid_inputs = {
        1: '1',
        'abc': 'abc'
    }
    invalid_inputs = {
        '': ['This field may not be blank.']
    }
    outputs = {
        1: '1',
        'abc': 'abc'
    }
    field = fields.CharField()


class TestEmailField(FieldValues):
    """
    Valid and invalid values for `EmailField`.
    """
    valid_inputs = {
        'example@example.com': 'example@example.com',
        ' example@example.com ': 'example@example.com',
    }
    invalid_inputs = {
        'examplecom': ['Enter a valid email address.']
    }
    outputs = {}
    field = fields.EmailField()


class TestRegexField(FieldValues):
    """
    Valid and invalid values for `RegexField`.
    """
    valid_inputs = {
        'a9': 'a9',
    }
    invalid_inputs = {
        'A9': ["This value does not match the required pattern."]
    }
    outputs = {}
    field = fields.RegexField(regex='[a-z][0-9]')


class TestSlugField(FieldValues):
    """
    Valid and invalid values for `SlugField`.
    """
    valid_inputs = {
        'slug-99': 'slug-99',
    }
    invalid_inputs = {
        'slug 99': ["Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens."]
    }
    outputs = {}
    field = fields.SlugField()


class TestURLField(FieldValues):
    """
    Valid and invalid values for `URLField`.
    """
    valid_inputs = {
        'http://example.com': 'http://example.com',
    }
    invalid_inputs = {
        'example.com': ['Enter a valid URL.']
    }
    outputs = {}
    field = fields.URLField()


# Number types...

class TestIntegerField(FieldValues):
    """
    Valid and invalid values for `IntegerField`.
    """
    valid_inputs = {
        '1': 1,
        '0': 0,
        1: 1,
        0: 0,
        1.0: 1,
        0.0: 0
    }
    invalid_inputs = {
        'abc': ['A valid integer is required.']
    }
    outputs = {
        '1': 1,
        '0': 0,
        1: 1,
        0: 0,
        1.0: 1,
        0.0: 0
    }
    field = fields.IntegerField()


class TestMinMaxIntegerField(FieldValues):
    """
    Valid and invalid values for `IntegerField` with min and max limits.
    """
    valid_inputs = {
        '1': 1,
        '3': 3,
        1: 1,
        3: 3,
    }
    invalid_inputs = {
        0: ['Ensure this value is greater than or equal to 1.'],
        4: ['Ensure this value is less than or equal to 3.'],
        '0': ['Ensure this value is greater than or equal to 1.'],
        '4': ['Ensure this value is less than or equal to 3.'],
    }
    outputs = {}
    field = fields.IntegerField(min_value=1, max_value=3)


class TestFloatField(FieldValues):
    """
    Valid and invalid values for `FloatField`.
    """
    valid_inputs = {
        '1': 1.0,
        '0': 0.0,
        1: 1.0,
        0: 0.0,
        1.0: 1.0,
        0.0: 0.0,
    }
    invalid_inputs = {
        'abc': ["A valid number is required."]
    }
    outputs = {
        '1': 1.0,
        '0': 0.0,
        1: 1.0,
        0: 0.0,
        1.0: 1.0,
        0.0: 0.0,
    }
    field = fields.FloatField()


class TestMinMaxFloatField(FieldValues):
    """
    Valid and invalid values for `FloatField` with min and max limits.
    """
    valid_inputs = {
        '1': 1,
        '3': 3,
        1: 1,
        3: 3,
        1.0: 1.0,
        3.0: 3.0,
    }
    invalid_inputs = {
        0.9: ['Ensure this value is greater than or equal to 1.'],
        3.1: ['Ensure this value is less than or equal to 3.'],
        '0.0': ['Ensure this value is greater than or equal to 1.'],
        '3.1': ['Ensure this value is less than or equal to 3.'],
    }
    outputs = {}
    field = fields.FloatField(min_value=1, max_value=3)


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
    }
    invalid_inputs = (
        ('abc', ["A valid number is required."]),
        (Decimal('Nan'), ["A valid number is required."]),
        (Decimal('Inf'), ["A valid number is required."]),
        ('12.345', ["Ensure that there are no more than 3 digits in total."]),
        ('0.01', ["Ensure that there are no more than 1 decimal places."]),
        (123, ["Ensure that there are no more than 2 digits before the decimal point."])
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
        Decimal('0.04'): '0.0',
    }
    field = fields.DecimalField(max_digits=3, decimal_places=1)


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
    field = fields.DecimalField(
        max_digits=3, decimal_places=1,
        min_value=10, max_value=20
    )


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
    field = fields.DecimalField(
        max_digits=3, decimal_places=1,
        coerce_to_string=False
    )


# Date & time fields...

class TestDateField(FieldValues):
    """
    Valid and invalid values for `DateField`.
    """
    valid_inputs = {
        '2001-01-01': datetime.date(2001, 1, 1),
        datetime.date(2001, 1, 1): datetime.date(2001, 1, 1),
    }
    invalid_inputs = {
        'abc': ['Date has wrong format. Use one of these formats instead: YYYY[-MM[-DD]]'],
        '2001-99-99': ['Date has wrong format. Use one of these formats instead: YYYY[-MM[-DD]]'],
        datetime.datetime(2001, 1, 1, 12, 00): ['Expected a date but got a datetime.'],
    }
    outputs = {
        datetime.date(2001, 1, 1): '2001-01-01',
    }
    field = fields.DateField()


class TestCustomInputFormatDateField(FieldValues):
    """
    Valid and invalid values for `DateField` with a cutom input format.
    """
    valid_inputs = {
        '1 Jan 2001': datetime.date(2001, 1, 1),
    }
    invalid_inputs = {
        '2001-01-01': ['Date has wrong format. Use one of these formats instead: DD [Jan-Dec] YYYY']
    }
    outputs = {}
    field = fields.DateField(input_formats=['%d %b %Y'])


class TestCustomOutputFormatDateField(FieldValues):
    """
    Values for `DateField` with a custom output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.date(2001, 1, 1): '01 Jan 2001'
    }
    field = fields.DateField(format='%d %b %Y')


class TestNoOutputFormatDateField(FieldValues):
    """
    Values for `DateField` with no output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.date(2001, 1, 1): datetime.date(2001, 1, 1)
    }
    field = fields.DateField(format=None)


class TestDateTimeField(FieldValues):
    """
    Valid and invalid values for `DateTimeField`.
    """
    valid_inputs = {
        '2001-01-01 13:00': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        '2001-01-01T13:00': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        '2001-01-01T13:00Z': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        datetime.datetime(2001, 1, 1, 13, 00): datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()): datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()),
        # Note that 1.4 does not support timezone string parsing.
        '2001-01-01T14:00+01:00' if (django.VERSION > (1, 4)) else '2001-01-01T13:00Z': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC())
    }
    invalid_inputs = {
        'abc': ['Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]'],
        '2001-99-99T99:00': ['Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]'],
        datetime.date(2001, 1, 1): ['Expected a datetime but got a date.'],
    }
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): '2001-01-01T13:00:00',
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()): '2001-01-01T13:00:00Z',
    }
    field = fields.DateTimeField(default_timezone=timezone.UTC())


class TestCustomInputFormatDateTimeField(FieldValues):
    """
    Valid and invalid values for `DateTimeField` with a cutom input format.
    """
    valid_inputs = {
        '1:35pm, 1 Jan 2001': datetime.datetime(2001, 1, 1, 13, 35, tzinfo=timezone.UTC()),
    }
    invalid_inputs = {
        '2001-01-01T20:50': ['Datetime has wrong format. Use one of these formats instead: hh:mm[AM|PM], DD [Jan-Dec] YYYY']
    }
    outputs = {}
    field = fields.DateTimeField(default_timezone=timezone.UTC(), input_formats=['%I:%M%p, %d %b %Y'])


class TestCustomOutputFormatDateTimeField(FieldValues):
    """
    Values for `DateTimeField` with a custom output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): '01:00PM, 01 Jan 2001',
    }
    field = fields.DateTimeField(format='%I:%M%p, %d %b %Y')


class TestNoOutputFormatDateTimeField(FieldValues):
    """
    Values for `DateTimeField` with no output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): datetime.datetime(2001, 1, 1, 13, 00),
    }
    field = fields.DateTimeField(format=None)


class TestNaiveDateTimeField(FieldValues):
    """
    Valid and invalid values for `DateTimeField` with naive datetimes.
    """
    valid_inputs = {
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()): datetime.datetime(2001, 1, 1, 13, 00),
        '2001-01-01 13:00': datetime.datetime(2001, 1, 1, 13, 00),
    }
    invalid_inputs = {}
    outputs = {}
    field = fields.DateTimeField(default_timezone=None)


class TestTimeField(FieldValues):
    """
    Valid and invalid values for `TimeField`.
    """
    valid_inputs = {
        '13:00': datetime.time(13, 00),
        datetime.time(13, 00): datetime.time(13, 00),
    }
    invalid_inputs = {
        'abc': ['Time has wrong format. Use one of these formats instead: hh:mm[:ss[.uuuuuu]]'],
        '99:99': ['Time has wrong format. Use one of these formats instead: hh:mm[:ss[.uuuuuu]]'],
    }
    outputs = {
        datetime.time(13, 00): '13:00:00'
    }
    field = fields.TimeField()


class TestCustomInputFormatTimeField(FieldValues):
    """
    Valid and invalid values for `TimeField` with a custom input format.
    """
    valid_inputs = {
        '1:00pm': datetime.time(13, 00),
    }
    invalid_inputs = {
        '13:00': ['Time has wrong format. Use one of these formats instead: hh:mm[AM|PM]'],
    }
    outputs = {}
    field = fields.TimeField(input_formats=['%I:%M%p'])


class TestCustomOutputFormatTimeField(FieldValues):
    """
    Values for `TimeField` with a custom output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.time(13, 00): '01:00PM'
    }
    field = fields.TimeField(format='%I:%M%p')


class TestNoOutputFormatTimeField(FieldValues):
    """
    Values for `TimeField` with a no output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.time(13, 00): datetime.time(13, 00)
    }
    field = fields.TimeField(format=None)


# Choice types...

class TestChoiceField(FieldValues):
    """
    Valid and invalid values for `ChoiceField`.
    """
    valid_inputs = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }
    invalid_inputs = {
        'amazing': ['`amazing` is not a valid choice.']
    }
    outputs = {
        'good': 'good'
    }
    field = fields.ChoiceField(
        choices=[
            ('poor', 'Poor quality'),
            ('medium', 'Medium quality'),
            ('good', 'Good quality'),
        ]
    )


class TestChoiceFieldWithType(FieldValues):
    """
    Valid and invalid values for a `Choice` field that uses an integer type,
    instead of a char type.
    """
    valid_inputs = {
        '1': 1,
        3: 3,
    }
    invalid_inputs = {
        5: ['`5` is not a valid choice.'],
        'abc': ['`abc` is not a valid choice.']
    }
    outputs = {
        '1': 1,
        1: 1
    }
    field = fields.ChoiceField(
        choices=[
            (1, 'Poor quality'),
            (2, 'Medium quality'),
            (3, 'Good quality'),
        ]
    )


class TestChoiceFieldWithListChoices(FieldValues):
    """
    Valid and invalid values for a `Choice` field that uses a flat list for the
    choices, rather than a list of pairs of (`value`, `description`).
    """
    valid_inputs = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }
    invalid_inputs = {
        'awful': ['`awful` is not a valid choice.']
    }
    outputs = {
        'good': 'good'
    }
    field = fields.ChoiceField(choices=('poor', 'medium', 'good'))


class TestMultipleChoiceField(FieldValues):
    """
    Valid and invalid values for `MultipleChoiceField`.
    """
    valid_inputs = {
        (): set(),
        ('aircon',): set(['aircon']),
        ('aircon', 'manual'): set(['aircon', 'manual']),
    }
    invalid_inputs = {
        'abc': ['Expected a list of items but got type `str`'],
        ('aircon', 'incorrect'): ['`incorrect` is not a valid choice.']
    }
    outputs = [
        (['aircon', 'manual'], set(['aircon', 'manual']))
    ]
    field = fields.MultipleChoiceField(
        choices=[
            ('aircon', 'AirCon'),
            ('manual', 'Manual drive'),
            ('diesel', 'Diesel'),
        ]
    )
