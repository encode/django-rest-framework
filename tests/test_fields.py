from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers
import datetime
import django
import pytest
import uuid


# Tests for field keyword arguments and core functionality.
# ---------------------------------------------------------

class TestEmpty:
    """
    Tests for `required`, `allow_null`, `allow_blank`, `default`.
    """
    def test_required(self):
        """
        By default a field must be included in the input.
        """
        field = serializers.IntegerField()
        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation()
        assert exc_info.value.detail == ['This field is required.']

    def test_not_required(self):
        """
        If `required=False` then a field may be omitted from the input.
        """
        field = serializers.IntegerField(required=False)
        with pytest.raises(serializers.SkipField):
            field.run_validation()

    def test_disallow_null(self):
        """
        By default `None` is not a valid input.
        """
        field = serializers.IntegerField()
        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation(None)
        assert exc_info.value.detail == ['This field may not be null.']

    def test_allow_null(self):
        """
        If `allow_null=True` then `None` is a valid input.
        """
        field = serializers.IntegerField(allow_null=True)
        output = field.run_validation(None)
        assert output is None

    def test_disallow_blank(self):
        """
        By default '' is not a valid input.
        """
        field = serializers.CharField()
        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation('')
        assert exc_info.value.detail == ['This field may not be blank.']

    def test_allow_blank(self):
        """
        If `allow_blank=True` then '' is a valid input.
        """
        field = serializers.CharField(allow_blank=True)
        output = field.run_validation('')
        assert output == ''

    def test_default(self):
        """
        If `default` is set, then omitted values get the default input.
        """
        field = serializers.IntegerField(default=123)
        output = field.run_validation()
        assert output is 123


class TestSource:
    def test_source(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.CharField(source='other')
        serializer = ExampleSerializer(data={'example_field': 'abc'})
        assert serializer.is_valid()
        assert serializer.validated_data == {'other': 'abc'}

    def test_redundant_source(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.CharField(source='example_field')
        with pytest.raises(AssertionError) as exc_info:
            ExampleSerializer().fields
        assert str(exc_info.value) == (
            "It is redundant to specify `source='example_field'` on field "
            "'CharField' in serializer 'ExampleSerializer', because it is the "
            "same as the field name. Remove the `source` keyword argument."
        )


class TestReadOnly:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            read_only = serializers.ReadOnlyField()
            writable = serializers.IntegerField()
        self.Serializer = TestSerializer

    def test_validate_read_only(self):
        """
        Read-only serializers.should not be included in validation.
        """
        data = {'read_only': 123, 'writable': 456}
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'writable': 456}

    def test_serialize_read_only(self):
        """
        Read-only serializers.should be serialized.
        """
        instance = {'read_only': 123, 'writable': 456}
        serializer = self.Serializer(instance)
        assert serializer.data == {'read_only': 123, 'writable': 456}


class TestWriteOnly:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            write_only = serializers.IntegerField(write_only=True)
            readable = serializers.IntegerField()
        self.Serializer = TestSerializer

    def test_validate_write_only(self):
        """
        Write-only serializers.should be included in validation.
        """
        data = {'write_only': 123, 'readable': 456}
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'write_only': 123, 'readable': 456}

    def test_serialize_write_only(self):
        """
        Write-only serializers.should not be serialized.
        """
        instance = {'write_only': 123, 'readable': 456}
        serializer = self.Serializer(instance)
        assert serializer.data == {'readable': 456}


class TestInitial:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            initial_field = serializers.IntegerField(initial=123)
            blank_field = serializers.IntegerField()
        self.serializer = TestSerializer()

    def test_initial(self):
        """
        Initial values should be included when serializing a new representation.
        """
        assert self.serializer.data == {
            'initial_field': 123,
            'blank_field': None
        }


class TestLabel:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            labeled = serializers.IntegerField(label='My label')
        self.serializer = TestSerializer()

    def test_label(self):
        """
        A field's label may be set with the `label` argument.
        """
        fields = self.serializer.fields
        assert fields['labeled'].label == 'My label'


class TestInvalidErrorKey:
    def setup(self):
        class ExampleField(serializers.Field):
            def to_native(self, data):
                self.fail('incorrect')
        self.field = ExampleField()

    def test_invalid_error_key(self):
        """
        If a field raises a validation error, but does not have a corresponding
        error message, then raise an appropriate assertion error.
        """
        with pytest.raises(AssertionError) as exc_info:
            self.field.to_native(123)
        expected = (
            'ValidationError raised by `ExampleField`, but error key '
            '`incorrect` does not exist in the `error_messages` dictionary.'
        )
        assert str(exc_info.value) == expected


class TestBooleanHTMLInput:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            archived = serializers.BooleanField()
        self.Serializer = TestSerializer

    def test_empty_html_checkbox(self):
        """
        HTML checkboxes do not send any value, but should be treated
        as `False` by BooleanField.
        """
        # This class mocks up a dictionary like object, that behaves
        # as if it was returned for multipart or urlencoded data.
        class MockHTMLDict(dict):
            getlist = None
        serializer = self.Serializer(data=MockHTMLDict())
        assert serializer.is_valid()
        assert serializer.validated_data == {'archived': False}


class MockHTMLDict(dict):
    """
    This class mocks up a dictionary like object, that behaves
    as if it was returned for multipart or urlencoded data.
    """
    getlist = None


class TestHTMLInput:
    def test_empty_html_charfield(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(default='happy')

        serializer = TestSerializer(data=MockHTMLDict())
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': 'happy'}

    def test_empty_html_charfield_allow_null(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(allow_null=True)

        serializer = TestSerializer(data=MockHTMLDict({'message': ''}))
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': None}

    def test_empty_html_datefield_allow_null(self):
        class TestSerializer(serializers.Serializer):
            expiry = serializers.DateField(allow_null=True)

        serializer = TestSerializer(data=MockHTMLDict({'expiry': ''}))
        assert serializer.is_valid()
        assert serializer.validated_data == {'expiry': None}

    def test_empty_html_charfield_allow_null_allow_blank(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(allow_null=True, allow_blank=True)

        serializer = TestSerializer(data=MockHTMLDict({'message': ''}))
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': ''}

    def test_empty_html_charfield_required_false(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(required=False)

        serializer = TestSerializer(data=MockHTMLDict())
        assert serializer.is_valid()
        assert serializer.validated_data == {}


class TestCreateOnlyDefault:
    def setup(self):
        default = serializers.CreateOnlyDefault('2001-01-01')

        class TestSerializer(serializers.Serializer):
            published = serializers.HiddenField(default=default)
            text = serializers.CharField()
        self.Serializer = TestSerializer

    def test_create_only_default_is_provided(self):
        serializer = self.Serializer(data={'text': 'example'})
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'text': 'example', 'published': '2001-01-01'
        }

    def test_create_only_default_is_not_provided_on_update(self):
        instance = {
            'text': 'example', 'published': '2001-01-01'
        }
        serializer = self.Serializer(instance, data={'text': 'example'})
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'text': 'example',
        }


# Tests for field input and output values.
# ----------------------------------------

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
            with pytest.raises(serializers.ValidationError) as exc_info:
                self.field.run_validation(input_value)
            assert exc_info.value.detail == expected_failure

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
        'foo': ['`foo` is not a valid boolean.'],
        None: ['This field may not be null.']
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
    field = serializers.BooleanField()


class TestNullBooleanField(FieldValues):
    """
    Valid and invalid values for `BooleanField`.
    """
    valid_inputs = {
        'true': True,
        'false': False,
        'null': None,
        True: True,
        False: False,
        None: None
    }
    invalid_inputs = {
        'foo': ['`foo` is not a valid boolean.'],
    }
    outputs = {
        'true': True,
        'false': False,
        'null': None,
        True: True,
        False: False,
        None: None,
        'other': True
    }
    field = serializers.NullBooleanField()


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
    field = serializers.CharField()


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
    field = serializers.EmailField()


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
    field = serializers.RegexField(regex='[a-z][0-9]')


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
    field = serializers.SlugField()


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
    field = serializers.URLField()


class TestUUIDField(FieldValues):
    """
    Valid and invalid values for `UUIDField`.
    """
    valid_inputs = {
        '825d7aeb-05a9-45b5-a5b7-05df87923cda': uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'),
        '825d7aeb05a945b5a5b705df87923cda': uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda')
    }
    invalid_inputs = {
        '825d7aeb-05a9-45b5-a5b7': ['"825d7aeb-05a9-45b5-a5b7" is not a valid UUID.']
    }
    outputs = {
        uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'): '825d7aeb-05a9-45b5-a5b7-05df87923cda'
    }
    field = serializers.UUIDField()


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
    field = serializers.IntegerField()


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
    field = serializers.IntegerField(min_value=1, max_value=3)


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
    field = serializers.FloatField()


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
    field = serializers.FloatField(min_value=1, max_value=3)


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


# Date & time serializers...

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
        datetime.date(2001, 1, 1): '2001-01-01'
    }
    field = serializers.DateField()


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
    field = serializers.DateField(input_formats=['%d %b %Y'])


class TestCustomOutputFormatDateField(FieldValues):
    """
    Values for `DateField` with a custom output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.date(2001, 1, 1): '01 Jan 2001'
    }
    field = serializers.DateField(format='%d %b %Y')


class TestNoOutputFormatDateField(FieldValues):
    """
    Values for `DateField` with no output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.date(2001, 1, 1): datetime.date(2001, 1, 1)
    }
    field = serializers.DateField(format=None)


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
        # Django 1.4 does not support timezone string parsing.
        '2001-01-01T14:00+01:00' if (django.VERSION > (1, 4)) else '2001-01-01T13:00Z': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC())
    }
    invalid_inputs = {
        'abc': ['Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]'],
        '2001-99-99T99:00': ['Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z]'],
        datetime.date(2001, 1, 1): ['Expected a datetime but got a date.'],
    }
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): '2001-01-01T13:00:00',
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=timezone.UTC()): '2001-01-01T13:00:00Z'
    }
    field = serializers.DateTimeField(default_timezone=timezone.UTC())


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
    field = serializers.DateTimeField(default_timezone=timezone.UTC(), input_formats=['%I:%M%p, %d %b %Y'])


class TestCustomOutputFormatDateTimeField(FieldValues):
    """
    Values for `DateTimeField` with a custom output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): '01:00PM, 01 Jan 2001',
    }
    field = serializers.DateTimeField(format='%I:%M%p, %d %b %Y')


class TestNoOutputFormatDateTimeField(FieldValues):
    """
    Values for `DateTimeField` with no output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): datetime.datetime(2001, 1, 1, 13, 00),
    }
    field = serializers.DateTimeField(format=None)


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
    field = serializers.DateTimeField(default_timezone=None)


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
    field = serializers.TimeField()


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
    field = serializers.TimeField(input_formats=['%I:%M%p'])


class TestCustomOutputFormatTimeField(FieldValues):
    """
    Values for `TimeField` with a custom output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.time(13, 00): '01:00PM'
    }
    field = serializers.TimeField(format='%I:%M%p')


class TestNoOutputFormatTimeField(FieldValues):
    """
    Values for `TimeField` with a no output format.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = {
        datetime.time(13, 00): datetime.time(13, 00)
    }
    field = serializers.TimeField(format=None)


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
        'good': 'good',
        '': ''
    }
    field = serializers.ChoiceField(
        choices=[
            ('poor', 'Poor quality'),
            ('medium', 'Medium quality'),
            ('good', 'Good quality'),
        ]
    )

    def test_allow_blank(self):
        """
        If `allow_blank=True` then '' is a valid input.
        """
        field = serializers.ChoiceField(
            allow_blank=True,
            choices=[
                ('poor', 'Poor quality'),
                ('medium', 'Medium quality'),
                ('good', 'Good quality'),
            ]
        )
        output = field.run_validation('')
        assert output == ''


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
    field = serializers.ChoiceField(
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
    field = serializers.ChoiceField(choices=('poor', 'medium', 'good'))


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
        'abc': ['Expected a list of items but got type `str`.'],
        ('aircon', 'incorrect'): ['`incorrect` is not a valid choice.']
    }
    outputs = [
        (['aircon', 'manual'], set(['aircon', 'manual']))
    ]
    field = serializers.MultipleChoiceField(
        choices=[
            ('aircon', 'AirCon'),
            ('manual', 'Manual drive'),
            ('diesel', 'Diesel'),
        ]
    )


# File serializers...

class MockFile:
    def __init__(self, name='', size=0, url=''):
        self.name = name
        self.size = size
        self.url = url

    def __eq__(self, other):
        return (
            isinstance(other, MockFile) and
            self.name == other.name and
            self.size == other.size and
            self.url == other.url
        )


class TestFileField(FieldValues):
    """
    Values for `FileField`.
    """
    valid_inputs = [
        (MockFile(name='example', size=10), MockFile(name='example', size=10))
    ]
    invalid_inputs = [
        ('invalid', ['The submitted data was not a file. Check the encoding type on the form.']),
        (MockFile(name='example.txt', size=0), ['The submitted file is empty.']),
        (MockFile(name='', size=10), ['No filename could be determined.']),
        (MockFile(name='x' * 100, size=10), ['Ensure this filename has at most 10 characters (it has 100).'])
    ]
    outputs = [
        (MockFile(name='example.txt', url='/example.txt'), '/example.txt'),
        ('', None)
    ]
    field = serializers.FileField(max_length=10)


class TestFieldFieldWithName(FieldValues):
    """
    Values for `FileField` with a filename output instead of URLs.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = [
        (MockFile(name='example.txt', url='/example.txt'), 'example.txt')
    ]
    field = serializers.FileField(use_url=False)


# Stub out mock Django `forms.ImageField` class so we don't *actually*
# call into it's regular validation, or require PIL for testing.
class FailImageValidation(object):
    def to_python(self, value):
        raise serializers.ValidationError(self.error_messages['invalid_image'])


class PassImageValidation(object):
    def to_python(self, value):
        return value


class TestInvalidImageField(FieldValues):
    """
    Values for an invalid `ImageField`.
    """
    valid_inputs = {}
    invalid_inputs = [
        (MockFile(name='example.txt', size=10), ['Upload a valid image. The file you uploaded was either not an image or a corrupted image.'])
    ]
    outputs = {}
    field = serializers.ImageField(_DjangoImageField=FailImageValidation)


class TestValidImageField(FieldValues):
    """
    Values for an valid `ImageField`.
    """
    valid_inputs = [
        (MockFile(name='example.txt', size=10), MockFile(name='example.txt', size=10))
    ]
    invalid_inputs = {}
    outputs = {}
    field = serializers.ImageField(_DjangoImageField=PassImageValidation)


# Composite serializers...

class TestListField(FieldValues):
    """
    Values for `ListField` with IntegerField as child.
    """
    valid_inputs = [
        ([1, 2, 3], [1, 2, 3]),
        (['1', '2', '3'], [1, 2, 3])
    ]
    invalid_inputs = [
        ('not a list', ['Expected a list of items but got type `str`']),
        ([1, 2, 'error'], ['A valid integer is required.'])
    ]
    outputs = [
        ([1, 2, 3], [1, 2, 3]),
        (['1', '2', '3'], [1, 2, 3])
    ]
    field = serializers.ListField(child=serializers.IntegerField())


class TestUnvalidatedListField(FieldValues):
    """
    Values for `ListField` with no `child` argument.
    """
    valid_inputs = [
        ([1, '2', True, [4, 5, 6]], [1, '2', True, [4, 5, 6]]),
    ]
    invalid_inputs = [
        ('not a list', ['Expected a list of items but got type `str`']),
    ]
    outputs = [
        ([1, '2', True, [4, 5, 6]], [1, '2', True, [4, 5, 6]]),
    ]
    field = serializers.ListField()


class TestDictField(FieldValues):
    """
    Values for `ListField` with CharField as child.
    """
    valid_inputs = [
        ({'a': 1, 'b': '2', 3: 3}, {'a': '1', 'b': '2', '3': '3'}),
    ]
    invalid_inputs = [
        ({'a': 1, 'b': None}, ['This field may not be null.']),
        ('not a dict', ['Expected a dictionary of items but got type `str`']),
    ]
    outputs = [
        ({'a': 1, 'b': '2', 3: 3}, {'a': '1', 'b': '2', '3': '3'}),
    ]
    field = serializers.DictField(child=serializers.CharField())


class TestUnvalidatedDictField(FieldValues):
    """
    Values for `ListField` with no `child` argument.
    """
    valid_inputs = [
        ({'a': 1, 'b': [4, 5, 6], 1: 123}, {'a': 1, 'b': [4, 5, 6], '1': 123}),
    ]
    invalid_inputs = [
        ('not a dict', ['Expected a dictionary of items but got type `str`']),
    ]
    outputs = [
        ({'a': 1, 'b': [4, 5, 6]}, {'a': 1, 'b': [4, 5, 6]}),
    ]
    field = serializers.DictField()


# Tests for FieldField.
# ---------------------

class MockRequest:
    def build_absolute_uri(self, value):
        return 'http://example.com' + value


class TestFileFieldContext:
    def test_fully_qualified_when_request_in_context(self):
        field = serializers.FileField(max_length=10)
        field._context = {'request': MockRequest()}
        obj = MockFile(name='example.txt', url='/example.txt')
        value = field.to_representation(obj)
        assert value == 'http://example.com/example.txt'


# Tests for SerializerMethodField.
# --------------------------------

class TestSerializerMethodField:
    def test_serializer_method_field(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.SerializerMethodField()

            def get_example_field(self, obj):
                return 'ran get_example_field(%d)' % obj['example_field']

        serializer = ExampleSerializer({'example_field': 123})
        assert serializer.data == {
            'example_field': 'ran get_example_field(123)'
        }

    def test_redundant_method_name(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.SerializerMethodField('get_example_field')

        with pytest.raises(AssertionError) as exc_info:
            ExampleSerializer().fields
        assert str(exc_info.value) == (
            "It is redundant to specify `get_example_field` on "
            "SerializerMethodField 'example_field' in serializer "
            "'ExampleSerializer', because it is the same as the default "
            "method name. Remove the `method_name` argument."
        )
