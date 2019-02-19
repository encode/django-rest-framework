import datetime
import os
import re
import unittest
import uuid
from decimal import ROUND_DOWN, ROUND_UP, Decimal

import pytest
import pytz
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import QueryDict
from django.test import TestCase, override_settings
from django.utils import six
from django.utils.timezone import activate, deactivate, override, utc

import rest_framework
from rest_framework import exceptions, serializers
from rest_framework.compat import ProhibitNullCharactersValidator
from rest_framework.fields import DjangoImageField, is_simple_callable

try:
    import typings
except ImportError:
    typings = False


# Tests for helper functions.
# ---------------------------

class TestIsSimpleCallable:

    def test_method(self):
        class Foo:
            @classmethod
            def classmethod(cls):
                pass

            def valid(self):
                pass

            def valid_kwargs(self, param='value'):
                pass

            def valid_vargs_kwargs(self, *args, **kwargs):
                pass

            def invalid(self, param):
                pass

        assert is_simple_callable(Foo.classmethod)

        # unbound methods
        assert not is_simple_callable(Foo.valid)
        assert not is_simple_callable(Foo.valid_kwargs)
        assert not is_simple_callable(Foo.valid_vargs_kwargs)
        assert not is_simple_callable(Foo.invalid)

        # bound methods
        assert is_simple_callable(Foo().valid)
        assert is_simple_callable(Foo().valid_kwargs)
        assert is_simple_callable(Foo().valid_vargs_kwargs)
        assert not is_simple_callable(Foo().invalid)

    def test_function(self):
        def simple():
            pass

        def valid(param='value', param2='value'):
            pass

        def valid_vargs_kwargs(*args, **kwargs):
            pass

        def invalid(param, param2='value'):
            pass

        assert is_simple_callable(simple)
        assert is_simple_callable(valid)
        assert is_simple_callable(valid_vargs_kwargs)
        assert not is_simple_callable(invalid)

    def test_4602_regression(self):
        from django.db import models

        class ChoiceModel(models.Model):
            choice_field = models.CharField(
                max_length=1, default='a',
                choices=(('a', 'A'), ('b', 'B')),
            )

            class Meta:
                app_label = 'tests'

        assert is_simple_callable(ChoiceModel().get_choice_field_display)

    @unittest.skipUnless(typings, 'requires python 3.5')
    def test_type_annotation(self):
        # The annotation will otherwise raise a syntax error in python < 3.5
        exec("def valid(param: str='value'):  pass", locals())
        valid = locals()['valid']

        assert is_simple_callable(valid)


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

    def test_callable_source(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.CharField(source='example_callable')

        class ExampleInstance(object):
            def example_callable(self):
                return 'example callable value'

        serializer = ExampleSerializer(ExampleInstance())
        assert serializer.data['example_field'] == 'example callable value'

    def test_callable_source_raises(self):
        class ExampleSerializer(serializers.Serializer):
            example_field = serializers.CharField(source='example_callable', read_only=True)

        class ExampleInstance(object):
            def example_callable(self):
                raise AttributeError('method call failed')

        with pytest.raises(ValueError) as exc_info:
            serializer = ExampleSerializer(ExampleInstance())
            serializer.data.items()

        assert 'method call failed' in str(exc_info.value)


class TestReadOnly:
    def setup(self):
        class TestSerializer(serializers.Serializer):
            read_only = serializers.ReadOnlyField(default="789")
            writable = serializers.IntegerField()
        self.Serializer = TestSerializer

    def test_writable_fields(self):
        """
        Read-only fields should not be writable, even with default ()
        """
        serializer = self.Serializer()
        assert len(serializer._writable_fields) == 1

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


class TestInitialWithCallable:
    def setup(self):
        def initial_value():
            return 123

        class TestSerializer(serializers.Serializer):
            initial_field = serializers.IntegerField(initial=initial_value)
        self.serializer = TestSerializer()

    def test_initial_should_accept_callable(self):
        """
        Follows the default ``Field.initial`` behaviour where they accept a
        callable to produce the initial value"""
        assert self.serializer.data == {
            'initial_field': 123,
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
    def test_empty_html_checkbox(self):
        """
        HTML checkboxes do not send any value, but should be treated
        as `False` by BooleanField.
        """
        class TestSerializer(serializers.Serializer):
            archived = serializers.BooleanField()

        serializer = TestSerializer(data=QueryDict(''))
        assert serializer.is_valid()
        assert serializer.validated_data == {'archived': False}

    def test_empty_html_checkbox_not_required(self):
        """
        HTML checkboxes do not send any value, but should be treated
        as `False` by BooleanField, even if the field is required=False.
        """
        class TestSerializer(serializers.Serializer):
            archived = serializers.BooleanField(required=False)

        serializer = TestSerializer(data=QueryDict(''))
        assert serializer.is_valid()
        assert serializer.validated_data == {'archived': False}


class TestHTMLInput:
    def test_empty_html_charfield_with_default(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(default='happy')

        serializer = TestSerializer(data=QueryDict(''))
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': 'happy'}

    def test_empty_html_charfield_without_default(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(allow_blank=True)

        serializer = TestSerializer(data=QueryDict('message='))
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': ''}

    def test_empty_html_charfield_without_default_not_required(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(allow_blank=True, required=False)

        serializer = TestSerializer(data=QueryDict('message='))
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': ''}

    def test_empty_html_integerfield(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.IntegerField(default=123)

        serializer = TestSerializer(data=QueryDict('message='))
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': 123}

    def test_empty_html_uuidfield_with_default(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.UUIDField(default=uuid.uuid4)

        serializer = TestSerializer(data=QueryDict('message='))
        assert serializer.is_valid()
        assert list(serializer.validated_data) == ['message']

    def test_empty_html_uuidfield_with_optional(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.UUIDField(required=False)

        serializer = TestSerializer(data=QueryDict('message='))
        assert serializer.is_valid()
        assert list(serializer.validated_data) == []

    def test_empty_html_charfield_allow_null(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(allow_null=True)

        serializer = TestSerializer(data=QueryDict('message='))
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': None}

    def test_empty_html_datefield_allow_null(self):
        class TestSerializer(serializers.Serializer):
            expiry = serializers.DateField(allow_null=True)

        serializer = TestSerializer(data=QueryDict('expiry='))
        assert serializer.is_valid()
        assert serializer.validated_data == {'expiry': None}

    def test_empty_html_charfield_allow_null_allow_blank(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(allow_null=True, allow_blank=True)

        serializer = TestSerializer(data=QueryDict('message='))
        assert serializer.is_valid()
        assert serializer.validated_data == {'message': ''}

    def test_empty_html_charfield_required_false(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.CharField(required=False)

        serializer = TestSerializer(data=QueryDict(''))
        assert serializer.is_valid()
        assert serializer.validated_data == {}

    def test_querydict_list_input(self):
        class TestSerializer(serializers.Serializer):
            scores = serializers.ListField(child=serializers.IntegerField())

        serializer = TestSerializer(data=QueryDict('scores=1&scores=3'))
        assert serializer.is_valid()
        assert serializer.validated_data == {'scores': [1, 3]}

    def test_querydict_list_input_only_one_input(self):
        class TestSerializer(serializers.Serializer):
            scores = serializers.ListField(child=serializers.IntegerField())

        serializer = TestSerializer(data=QueryDict('scores=1&'))
        assert serializer.is_valid()
        assert serializer.validated_data == {'scores': [1]}

    def test_querydict_list_input_no_values_uses_default(self):
        """
        When there are no values passed in, and default is set
        The field should return the default value
        """
        class TestSerializer(serializers.Serializer):
            a = serializers.IntegerField(required=True)
            scores = serializers.ListField(default=lambda: [1, 3])

        serializer = TestSerializer(data=QueryDict('a=1&'))
        assert serializer.is_valid()
        assert serializer.validated_data == {'a': 1, 'scores': [1, 3]}

    def test_querydict_list_input_supports_indexed_keys(self):
        """
        When data is passed in the format `scores[0]=1&scores[1]=3`
        The field should return the correct list, ignoring the default
        """
        class TestSerializer(serializers.Serializer):
            scores = serializers.ListField(default=lambda: [1, 3])

        serializer = TestSerializer(data=QueryDict("scores[0]=5&scores[1]=6"))
        assert serializer.is_valid()
        assert serializer.validated_data == {'scores': ['5', '6']}

    def test_querydict_list_input_no_values_no_default_and_not_required(self):
        """
        When there are no keys passed, there is no default, and required=False
        The field should be skipped
        """
        class TestSerializer(serializers.Serializer):
            scores = serializers.ListField(required=False)

        serializer = TestSerializer(data=QueryDict(''))
        assert serializer.is_valid()
        assert serializer.validated_data == {}

    def test_querydict_list_input_posts_key_but_no_values(self):
        """
        When there are no keys passed, there is no default, and required=False
        The field should return an array of 1 item, blank
        """
        class TestSerializer(serializers.Serializer):
            scores = serializers.ListField(required=False)

        serializer = TestSerializer(data=QueryDict('scores=&'))
        assert serializer.is_valid()
        assert serializer.validated_data == {'scores': ['']}


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

    def test_create_only_default_callable_sets_context(self):
        """
        CreateOnlyDefault instances with a callable default should set_context
        on the callable if possible
        """
        class TestCallableDefault:
            def set_context(self, serializer_field):
                self.field = serializer_field

            def __call__(self):
                return "success" if hasattr(self, 'field') else "failure"

        class TestSerializer(serializers.Serializer):
            context_set = serializers.CharField(default=serializers.CreateOnlyDefault(TestCallableDefault()))

        serializer = TestSerializer(data={})
        assert serializer.is_valid()
        assert serializer.validated_data['context_set'] == 'success'


class Test5087Regression:
    def test_parent_binding(self):
        parent = serializers.Serializer()
        field = serializers.CharField()

        assert field.root is field
        field.bind('name', parent)
        assert field.root is parent


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
            assert self.field.run_validation(input_value) == expected_output, \
                'input value: {}'.format(repr(input_value))

    def test_invalid_inputs(self):
        """
        Ensure that invalid values raise the expected validation error.
        """
        for input_value, expected_failure in get_items(self.invalid_inputs):
            with pytest.raises(serializers.ValidationError) as exc_info:
                self.field.run_validation(input_value)
            assert exc_info.value.detail == expected_failure, \
                'input value: {}'.format(repr(input_value))

    def test_outputs(self):
        for output_value, expected_output in get_items(self.outputs):
            assert self.field.to_representation(output_value) == expected_output, \
                'output value: {}'.format(repr(output_value))


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
        'foo': ['Must be a valid boolean.'],
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

    def test_disallow_unhashable_collection_types(self):
        inputs = (
            [],
            {},
        )
        field = self.field
        for input_value in inputs:
            with pytest.raises(serializers.ValidationError) as exc_info:
                field.run_validation(input_value)
            expected = ['Must be a valid boolean.'.format(input_value)]
            assert exc_info.value.detail == expected


class TestNullBooleanField(TestBooleanField):
    """
    Valid and invalid values for `NullBooleanField`.
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
        'foo': ['Must be a valid boolean.'],
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


class TestNullableBooleanField(TestNullBooleanField):
    """
    Valid and invalid values for `BooleanField` when `allow_null=True`.
    """

    @property
    def field(self):
        return serializers.BooleanField(allow_null=True)


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
        (): ['Not a valid string.'],
        True: ['Not a valid string.'],
        '': ['This field may not be blank.']
    }
    outputs = {
        1: '1',
        'abc': 'abc'
    }
    field = serializers.CharField()

    def test_trim_whitespace_default(self):
        field = serializers.CharField()
        assert field.to_internal_value(' abc ') == 'abc'

    def test_trim_whitespace_disabled(self):
        field = serializers.CharField(trim_whitespace=False)
        assert field.to_internal_value(' abc ') == ' abc '

    def test_disallow_blank_with_trim_whitespace(self):
        field = serializers.CharField(allow_blank=False, trim_whitespace=True)

        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation('   ')
        assert exc_info.value.detail == ['This field may not be blank.']

    @pytest.mark.skipif(ProhibitNullCharactersValidator is None, reason="Skipped on Django < 2.0")
    def test_null_bytes(self):
        field = serializers.CharField()

        for value in ('\0', 'foo\0', '\0foo', 'foo\0foo'):
            with pytest.raises(serializers.ValidationError) as exc_info:
                field.run_validation(value)
            assert exc_info.value.detail == [
                'Null characters are not allowed.'
            ]

    def test_iterable_validators(self):
        """
        Ensure `validators` parameter is compatible with reasonable iterables.
        """
        value = 'example'

        for validators in ([], (), set()):
            field = serializers.CharField(validators=validators)
            field.run_validation(value)

        def raise_exception(value):
            raise exceptions.ValidationError('Raised error')

        for validators in ([raise_exception], (raise_exception,), set([raise_exception])):
            field = serializers.CharField(validators=validators)
            with pytest.raises(serializers.ValidationError) as exc_info:
                field.run_validation(value)
            assert exc_info.value.detail == ['Raised error']


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


class TestiCompiledRegexField(FieldValues):
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
    field = serializers.RegexField(regex=re.compile('[a-z][0-9]'))


class TestSlugField(FieldValues):
    """
    Valid and invalid values for `SlugField`.
    """
    valid_inputs = {
        'slug-99': 'slug-99',
    }
    invalid_inputs = {
        'slug 99': ['Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.']
    }
    outputs = {}
    field = serializers.SlugField()

    def test_allow_unicode_true(self):
        field = serializers.SlugField(allow_unicode=True)

        validation_error = False
        try:
            field.run_validation(u'slug-99-\u0420')
        except serializers.ValidationError:
            validation_error = True

        assert not validation_error


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
        '825d7aeb05a945b5a5b705df87923cda': uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'),
        'urn:uuid:213b7d9b-244f-410d-828c-dabce7a2615d': uuid.UUID('213b7d9b-244f-410d-828c-dabce7a2615d'),
        284758210125106368185219588917561929842: uuid.UUID('d63a6fb6-88d5-40c7-a91c-9edf73283072')
    }
    invalid_inputs = {
        '825d7aeb-05a9-45b5-a5b7': ['Must be a valid UUID.'],
        (1, 2, 3): ['Must be a valid UUID.']
    }
    outputs = {
        uuid.UUID('825d7aeb-05a9-45b5-a5b7-05df87923cda'): '825d7aeb-05a9-45b5-a5b7-05df87923cda'
    }
    field = serializers.UUIDField()

    def _test_format(self, uuid_format, formatted_uuid_0):
        field = serializers.UUIDField(format=uuid_format)
        assert field.to_representation(uuid.UUID(int=0)) == formatted_uuid_0
        assert field.to_internal_value(formatted_uuid_0) == uuid.UUID(int=0)

    def test_formats(self):
        self._test_format('int', 0)
        self._test_format('hex_verbose', '00000000-0000-0000-0000-000000000000')
        self._test_format('urn', 'urn:uuid:00000000-0000-0000-0000-000000000000')
        self._test_format('hex', '0' * 32)


class TestIPAddressField(FieldValues):
    """
    Valid and invalid values for `IPAddressField`
    """
    valid_inputs = {
        '127.0.0.1': '127.0.0.1',
        '192.168.33.255': '192.168.33.255',
        '2001:0db8:85a3:0042:1000:8a2e:0370:7334': '2001:db8:85a3:42:1000:8a2e:370:7334',
        '2001:cdba:0:0:0:0:3257:9652': '2001:cdba::3257:9652',
        '2001:cdba::3257:9652': '2001:cdba::3257:9652'
    }
    invalid_inputs = {
        '127001': ['Enter a valid IPv4 or IPv6 address.'],
        '127.122.111.2231': ['Enter a valid IPv4 or IPv6 address.'],
        '2001:::9652': ['Enter a valid IPv4 or IPv6 address.'],
        '2001:0db8:85a3:0042:1000:8a2e:0370:73341': ['Enter a valid IPv4 or IPv6 address.'],
        1000: ['Enter a valid IPv4 or IPv6 address.'],
    }
    outputs = {}
    field = serializers.IPAddressField()


class TestIPv4AddressField(FieldValues):
    """
    Valid and invalid values for `IPAddressField`
    """
    valid_inputs = {
        '127.0.0.1': '127.0.0.1',
        '192.168.33.255': '192.168.33.255',
    }
    invalid_inputs = {
        '127001': ['Enter a valid IPv4 address.'],
        '127.122.111.2231': ['Enter a valid IPv4 address.'],
    }
    outputs = {}
    field = serializers.IPAddressField(protocol='IPv4')


class TestIPv6AddressField(FieldValues):
    """
    Valid and invalid values for `IPAddressField`
    """
    valid_inputs = {
        '2001:0db8:85a3:0042:1000:8a2e:0370:7334': '2001:db8:85a3:42:1000:8a2e:370:7334',
        '2001:cdba:0:0:0:0:3257:9652': '2001:cdba::3257:9652',
        '2001:cdba::3257:9652': '2001:cdba::3257:9652'
    }
    invalid_inputs = {
        '2001:::9652': ['Enter a valid IPv4 or IPv6 address.'],
        '2001:0db8:85a3:0042:1000:8a2e:0370:73341': ['Enter a valid IPv4 or IPv6 address.'],
    }
    outputs = {}
    field = serializers.IPAddressField(protocol='IPv6')


class TestFilePathField(FieldValues):
    """
    Valid and invalid values for `FilePathField`
    """

    valid_inputs = {
        __file__: __file__,
    }
    invalid_inputs = {
        'wrong_path': ['"wrong_path" is not a valid path choice.']
    }
    outputs = {
    }
    field = serializers.FilePathField(
        path=os.path.abspath(os.path.dirname(__file__))
    )


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
        0.0: 0,
        '1.0': 1
    }
    invalid_inputs = {
        0.5: ['A valid integer is required.'],
        'abc': ['A valid integer is required.'],
        '0.5': ['A valid integer is required.']
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
        assert field.to_internal_value('1,1') == Decimal('1.1')

    @override_settings(USE_L10N=True, LANGUAGE_CODE='pl')
    def test_to_representation(self):
        field = serializers.DecimalField(max_digits=2, decimal_places=1, localize=True)
        assert field.to_representation(Decimal('1.1')) == '1,1'

    def test_localize_forces_coerce_to_string(self):
        field = serializers.DecimalField(max_digits=2, decimal_places=1, coerce_to_string=False, localize=True)
        assert isinstance(field.to_representation(Decimal('1.1')), six.string_types)


class TestQuantizedValueForDecimal(TestCase):
    def test_int_quantized_value_for_decimal(self):
        field = serializers.DecimalField(max_digits=4, decimal_places=2)
        value = field.to_internal_value(12).as_tuple()
        expected_digit_tuple = (0, (1, 2, 0, 0), -2)
        assert value == expected_digit_tuple

    def test_string_quantized_value_for_decimal(self):
        field = serializers.DecimalField(max_digits=4, decimal_places=2)
        value = field.to_internal_value('12').as_tuple()
        expected_digit_tuple = (0, (1, 2, 0, 0), -2)
        assert value == expected_digit_tuple

    def test_part_precision_string_quantized_value_for_decimal(self):
        field = serializers.DecimalField(max_digits=4, decimal_places=2)
        value = field.to_internal_value('12.0').as_tuple()
        expected_digit_tuple = (0, (1, 2, 0, 0), -2)
        assert value == expected_digit_tuple


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


class TestRoundingDecimalField(TestCase):
    def test_valid_rounding(self):
        field = serializers.DecimalField(max_digits=4, decimal_places=2, rounding=ROUND_UP)
        assert field.to_representation(Decimal('1.234')) == '1.24'

        field = serializers.DecimalField(max_digits=4, decimal_places=2, rounding=ROUND_DOWN)
        assert field.to_representation(Decimal('1.234')) == '1.23'

    def test_invalid_rounding(self):
        with pytest.raises(AssertionError) as excinfo:
            serializers.DecimalField(max_digits=1, decimal_places=1, rounding='ROUND_UNKNOWN')
        assert 'Invalid rounding option' in str(excinfo.value)


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
        'abc': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'],
        '2001-99-99': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'],
        '2001-01': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'],
        '2001': ['Date has wrong format. Use one of these formats instead: YYYY-MM-DD.'],
        datetime.datetime(2001, 1, 1, 12, 00): ['Expected a date but got a datetime.'],
    }
    outputs = {
        datetime.date(2001, 1, 1): '2001-01-01',
        '2001-01-01': '2001-01-01',
        six.text_type('2016-01-10'): '2016-01-10',
        None: None,
        '': None,
    }
    field = serializers.DateField()


class TestCustomInputFormatDateField(FieldValues):
    """
    Valid and invalid values for `DateField` with a custom input format.
    """
    valid_inputs = {
        '1 Jan 2001': datetime.date(2001, 1, 1),
    }
    invalid_inputs = {
        '2001-01-01': ['Date has wrong format. Use one of these formats instead: DD [Jan-Dec] YYYY.']
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
        '2001-01-01 13:00': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc),
        '2001-01-01T13:00': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc),
        '2001-01-01T13:00Z': datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc),
        datetime.datetime(2001, 1, 1, 13, 00): datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc),
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc): datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc),
    }
    invalid_inputs = {
        'abc': ['Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'],
        '2001-99-99T99:00': ['Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'],
        '2018-08-16 22:00-24:00': ['Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'],
        datetime.date(2001, 1, 1): ['Expected a datetime but got a date.'],
        '9999-12-31T21:59:59.99990-03:00': ['Datetime value out of range.'],
    }
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): '2001-01-01T13:00:00Z',
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc): '2001-01-01T13:00:00Z',
        '2001-01-01T00:00:00': '2001-01-01T00:00:00',
        six.text_type('2016-01-10T00:00:00'): '2016-01-10T00:00:00',
        None: None,
        '': None,
    }
    field = serializers.DateTimeField(default_timezone=utc)


class TestCustomInputFormatDateTimeField(FieldValues):
    """
    Valid and invalid values for `DateTimeField` with a custom input format.
    """
    valid_inputs = {
        '1:35pm, 1 Jan 2001': datetime.datetime(2001, 1, 1, 13, 35, tzinfo=utc),
    }
    invalid_inputs = {
        '2001-01-01T20:50': ['Datetime has wrong format. Use one of these formats instead: hh:mm[AM|PM], DD [Jan-Dec] YYYY.']
    }
    outputs = {}
    field = serializers.DateTimeField(default_timezone=utc, input_formats=['%I:%M%p, %d %b %Y'])


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
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc): datetime.datetime(2001, 1, 1, 13, 00),
        '2001-01-01 13:00': datetime.datetime(2001, 1, 1, 13, 00),
    }
    invalid_inputs = {}
    outputs = {
        datetime.datetime(2001, 1, 1, 13, 00): '2001-01-01T13:00:00',
        datetime.datetime(2001, 1, 1, 13, 00, tzinfo=utc): '2001-01-01T13:00:00',
    }
    field = serializers.DateTimeField(default_timezone=None)


class TestTZWithDateTimeField(FieldValues):
    """
    Valid and invalid values for `DateTimeField` when not using UTC as the timezone.
    """
    @classmethod
    def setup_class(cls):
        # use class setup method, as class-level attribute will still be evaluated even if test is skipped
        kolkata = pytz.timezone('Asia/Kolkata')

        cls.valid_inputs = {
            '2016-12-19T10:00:00': kolkata.localize(datetime.datetime(2016, 12, 19, 10)),
            '2016-12-19T10:00:00+05:30': kolkata.localize(datetime.datetime(2016, 12, 19, 10)),
            datetime.datetime(2016, 12, 19, 10): kolkata.localize(datetime.datetime(2016, 12, 19, 10)),
        }
        cls.invalid_inputs = {}
        cls.outputs = {
            datetime.datetime(2016, 12, 19, 10): '2016-12-19T10:00:00+05:30',
            datetime.datetime(2016, 12, 19, 4, 30, tzinfo=utc): '2016-12-19T10:00:00+05:30',
        }
        cls.field = serializers.DateTimeField(default_timezone=kolkata)


@override_settings(TIME_ZONE='UTC', USE_TZ=True)
class TestDefaultTZDateTimeField(TestCase):
    """
    Test the current/default timezone handling in `DateTimeField`.
    """

    @classmethod
    def setup_class(cls):
        cls.field = serializers.DateTimeField()
        cls.kolkata = pytz.timezone('Asia/Kolkata')

    def test_default_timezone(self):
        assert self.field.default_timezone() == utc

    def test_current_timezone(self):
        assert self.field.default_timezone() == utc
        activate(self.kolkata)
        assert self.field.default_timezone() == self.kolkata
        deactivate()
        assert self.field.default_timezone() == utc


@pytest.mark.skipif(pytz is None, reason='pytz not installed')
@override_settings(TIME_ZONE='UTC', USE_TZ=True)
class TestCustomTimezoneForDateTimeField(TestCase):

    @classmethod
    def setup_class(cls):
        cls.kolkata = pytz.timezone('Asia/Kolkata')
        cls.date_format = '%d/%m/%Y %H:%M'

    def test_should_render_date_time_in_default_timezone(self):
        field = serializers.DateTimeField(default_timezone=self.kolkata, format=self.date_format)
        dt = datetime.datetime(2018, 2, 8, 14, 15, 16, tzinfo=pytz.utc)

        with override(self.kolkata):
            rendered_date = field.to_representation(dt)

        rendered_date_in_timezone = dt.astimezone(self.kolkata).strftime(self.date_format)

        assert rendered_date == rendered_date_in_timezone


class TestNaiveDayLightSavingTimeTimeZoneDateTimeField(FieldValues):
    """
    Invalid values for `DateTimeField` with datetime in DST shift (non-existing or ambiguous) and timezone with DST.
    Timezone America/New_York has DST shift from 2017-03-12T02:00:00 to 2017-03-12T03:00:00 and
     from 2017-11-05T02:00:00 to 2017-11-05T01:00:00 in 2017.
    """
    valid_inputs = {}
    invalid_inputs = {
        '2017-03-12T02:30:00': ['Invalid datetime for the timezone "America/New_York".'],
        '2017-11-05T01:30:00': ['Invalid datetime for the timezone "America/New_York".']
    }
    outputs = {}

    class MockTimezone:
        @staticmethod
        def localize(value, is_dst):
            raise pytz.InvalidTimeError()

        def __str__(self):
            return 'America/New_York'

    field = serializers.DateTimeField(default_timezone=MockTimezone())


class TestTimeField(FieldValues):
    """
    Valid and invalid values for `TimeField`.
    """
    valid_inputs = {
        '13:00': datetime.time(13, 00),
        datetime.time(13, 00): datetime.time(13, 00),
    }
    invalid_inputs = {
        'abc': ['Time has wrong format. Use one of these formats instead: hh:mm[:ss[.uuuuuu]].'],
        '99:99': ['Time has wrong format. Use one of these formats instead: hh:mm[:ss[.uuuuuu]].'],
    }
    outputs = {
        datetime.time(13, 0): '13:00:00',
        datetime.time(0, 0): '00:00:00',
        '00:00:00': '00:00:00',
        None: None,
        '': None,
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
        '13:00': ['Time has wrong format. Use one of these formats instead: hh:mm[AM|PM].'],
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


class TestMinMaxDurationField(FieldValues):
    """
    Valid and invalid values for `DurationField` with min and max limits.
    """
    valid_inputs = {
        '3 08:32:01.000123': datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123),
        86401: datetime.timedelta(days=1, seconds=1),
    }
    invalid_inputs = {
        3600: ['Ensure this value is greater than or equal to 1 day, 0:00:00.'],
        '4 08:32:01.000123': ['Ensure this value is less than or equal to 4 days, 0:00:00.'],
        '3600': ['Ensure this value is greater than or equal to 1 day, 0:00:00.'],
    }
    outputs = {}
    field = serializers.DurationField(min_value=datetime.timedelta(days=1), max_value=datetime.timedelta(days=4))


class TestDurationField(FieldValues):
    """
    Valid and invalid values for `DurationField`.
    """
    valid_inputs = {
        '13': datetime.timedelta(seconds=13),
        '3 08:32:01.000123': datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123),
        '08:01': datetime.timedelta(minutes=8, seconds=1),
        datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123): datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123),
        3600: datetime.timedelta(hours=1),
    }
    invalid_inputs = {
        'abc': ['Duration has wrong format. Use one of these formats instead: [DD] [HH:[MM:]]ss[.uuuuuu].'],
        '3 08:32 01.123': ['Duration has wrong format. Use one of these formats instead: [DD] [HH:[MM:]]ss[.uuuuuu].'],
    }
    outputs = {
        datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123): '3 08:32:01.000123',
    }
    field = serializers.DurationField()


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
        'amazing': ['"amazing" is not a valid choice.']
    }
    outputs = {
        'good': 'good',
        '': '',
        'amazing': 'amazing',
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

    def test_allow_null(self):
        """
        If `allow_null=True` then '' on HTML forms is treated as None.
        """
        field = serializers.ChoiceField(
            allow_null=True,
            choices=[
                1, 2, 3
            ]
        )
        field.field_name = 'example'
        value = field.get_value(QueryDict('example='))
        assert value is None
        output = field.run_validation(None)
        assert output is None

    def test_iter_options(self):
        """
        iter_options() should return a list of options and option groups.
        """
        field = serializers.ChoiceField(
            choices=[
                ('Numbers', ['integer', 'float']),
                ('Strings', ['text', 'email', 'url']),
                'boolean'
            ]
        )
        items = list(field.iter_options())

        assert items[0].start_option_group
        assert items[0].label == 'Numbers'
        assert items[1].value == 'integer'
        assert items[2].value == 'float'
        assert items[3].end_option_group

        assert items[4].start_option_group
        assert items[4].label == 'Strings'
        assert items[5].value == 'text'
        assert items[6].value == 'email'
        assert items[7].value == 'url'
        assert items[8].end_option_group

        assert items[9].value == 'boolean'

    def test_edit_choices(self):
        field = serializers.ChoiceField(
            allow_null=True,
            choices=[
                1, 2,
            ]
        )
        field.choices = [1]
        assert field.run_validation(1) is 1
        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation(2)
        assert exc_info.value.detail == ['"2" is not a valid choice.']


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
        5: ['"5" is not a valid choice.'],
        'abc': ['"abc" is not a valid choice.']
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
        'awful': ['"awful" is not a valid choice.']
    }
    outputs = {
        'good': 'good'
    }
    field = serializers.ChoiceField(choices=('poor', 'medium', 'good'))


class TestChoiceFieldWithGroupedChoices(FieldValues):
    """
    Valid and invalid values for a `Choice` field that uses a grouped list for the
    choices, rather than a list of pairs of (`value`, `description`).
    """
    valid_inputs = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }
    invalid_inputs = {
        'awful': ['"awful" is not a valid choice.']
    }
    outputs = {
        'good': 'good'
    }
    field = serializers.ChoiceField(
        choices=[
            (
                'Category',
                (
                    ('poor', 'Poor quality'),
                    ('medium', 'Medium quality'),
                ),
            ),
            ('good', 'Good quality'),
        ]
    )


class TestChoiceFieldWithMixedChoices(FieldValues):
    """
    Valid and invalid values for a `Choice` field that uses a single paired or
    grouped.
    """
    valid_inputs = {
        'poor': 'poor',
        'medium': 'medium',
        'good': 'good',
    }
    invalid_inputs = {
        'awful': ['"awful" is not a valid choice.']
    }
    outputs = {
        'good': 'good'
    }
    field = serializers.ChoiceField(
        choices=[
            (
                'Category',
                (
                    ('poor', 'Poor quality'),
                ),
            ),
            'medium',
            ('good', 'Good quality'),
        ]
    )


class TestMultipleChoiceField(FieldValues):
    """
    Valid and invalid values for `MultipleChoiceField`.
    """
    valid_inputs = {
        (): set(),
        ('aircon',): {'aircon'},
        ('aircon', 'manual'): {'aircon', 'manual'},
    }
    invalid_inputs = {
        'abc': ['Expected a list of items but got type "str".'],
        ('aircon', 'incorrect'): ['"incorrect" is not a valid choice.']
    }
    outputs = [
        (['aircon', 'manual', 'incorrect'], {'aircon', 'manual', 'incorrect'})
    ]
    field = serializers.MultipleChoiceField(
        choices=[
            ('aircon', 'AirCon'),
            ('manual', 'Manual drive'),
            ('diesel', 'Diesel'),
        ]
    )

    def test_against_partial_and_full_updates(self):
        field = serializers.MultipleChoiceField(choices=(('a', 'a'), ('b', 'b')))
        field.partial = False
        assert field.get_value(QueryDict({})) == []
        field.partial = True
        assert field.get_value(QueryDict({})) == rest_framework.fields.empty


class TestEmptyMultipleChoiceField(FieldValues):
    """
    Invalid values for `MultipleChoiceField(allow_empty=False)`.
    """
    valid_inputs = {
    }
    invalid_inputs = (
        ([], ['This selection may not be empty.']),
    )
    outputs = [
    ]
    field = serializers.MultipleChoiceField(
        choices=[
            ('consistency', 'Consistency'),
            ('availability', 'Availability'),
            ('partition', 'Partition tolerance'),
        ],
        allow_empty=False
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


def ext_validator(value):
    if not value.name.endswith('.png'):
        raise serializers.ValidationError('File extension is not allowed. Allowed extensions is png.')


# Stub out mock Django `forms.ImageField` class so we don't *actually*
# call into it's regular validation, or require PIL for testing.
class PassImageValidation(DjangoImageField):
    default_validators = [ext_validator]

    def to_python(self, value):
        return value


class FailImageValidation(PassImageValidation):
    def to_python(self, value):
        if value.name == 'badimage.png':
            raise serializers.ValidationError(self.error_messages['invalid_image'])
        return value


class TestInvalidImageField(FieldValues):
    """
    Values for an invalid `ImageField`.
    """
    valid_inputs = {}
    invalid_inputs = [
        (MockFile(name='badimage.png', size=10), ['Upload a valid image. The file you uploaded was either not an image or a corrupted image.']),
        (MockFile(name='goodimage.html', size=10), ['File extension is not allowed. Allowed extensions is png.'])
    ]
    outputs = {}
    field = serializers.ImageField(_DjangoImageField=FailImageValidation)


class TestValidImageField(FieldValues):
    """
    Values for an valid `ImageField`.
    """
    valid_inputs = [
        (MockFile(name='example.png', size=10), MockFile(name='example.png', size=10))
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
        (['1', '2', '3'], [1, 2, 3]),
        ([], [])
    ]
    invalid_inputs = [
        ('not a list', ['Expected a list of items but got type "str".']),
        ([1, 2, 'error', 'error'], {2: ['A valid integer is required.'], 3: ['A valid integer is required.']}),
        ({'one': 'two'}, ['Expected a list of items but got type "dict".'])
    ]
    outputs = [
        ([1, 2, 3], [1, 2, 3]),
        (['1', '2', '3'], [1, 2, 3])
    ]
    field = serializers.ListField(child=serializers.IntegerField())

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            serializers.ListField(child=serializers.IntegerField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )

    def test_collection_types_are_invalid_input(self):
        field = serializers.ListField(child=serializers.CharField())
        input_value = ({'one': 'two'})

        with pytest.raises(serializers.ValidationError) as exc_info:
            field.to_internal_value(input_value)
        assert exc_info.value.detail == ['Expected a list of items but got type "dict".']


class TestNestedListField(FieldValues):
    """
    Values for nested `ListField` with IntegerField as child.
    """
    valid_inputs = [
        ([[1, 2], [3]], [[1, 2], [3]]),
        ([[]], [[]])
    ]
    invalid_inputs = [
        (['not a list'], {0: ['Expected a list of items but got type "str".']}),
        ([[1, 2, 'error'], ['error']], {0: {2: ['A valid integer is required.']}, 1: {0: ['A valid integer is required.']}}),
        ([{'one': 'two'}], {0: ['Expected a list of items but got type "dict".']})
    ]
    outputs = [
        ([[1, 2], [3]], [[1, 2], [3]]),
    ]
    field = serializers.ListField(child=serializers.ListField(child=serializers.IntegerField()))


class TestEmptyListField(FieldValues):
    """
    Values for `ListField` with allow_empty=False flag.
    """
    valid_inputs = {}
    invalid_inputs = [
        ([], ['This list may not be empty.'])
    ]
    outputs = {}
    field = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class TestListFieldLengthLimit(FieldValues):
    valid_inputs = ()
    invalid_inputs = [
        ((0, 1), ['Ensure this field has at least 3 elements.']),
        ((0, 1, 2, 3, 4, 5), ['Ensure this field has no more than 4 elements.']),
    ]
    outputs = ()
    field = serializers.ListField(child=serializers.IntegerField(), min_length=3, max_length=4)


class TestUnvalidatedListField(FieldValues):
    """
    Values for `ListField` with no `child` argument.
    """
    valid_inputs = [
        ([1, '2', True, [4, 5, 6]], [1, '2', True, [4, 5, 6]]),
    ]
    invalid_inputs = [
        ('not a list', ['Expected a list of items but got type "str".']),
    ]
    outputs = [
        ([1, '2', True, [4, 5, 6]], [1, '2', True, [4, 5, 6]]),
    ]
    field = serializers.ListField()


class TestDictField(FieldValues):
    """
    Values for `DictField` with CharField as child.
    """
    valid_inputs = [
        ({'a': 1, 'b': '2', 3: 3}, {'a': '1', 'b': '2', '3': '3'}),
    ]
    invalid_inputs = [
        ({'a': 1, 'b': None, 'c': None}, {'b': ['This field may not be null.'], 'c': ['This field may not be null.']}),
        ('not a dict', ['Expected a dictionary of items but got type "str".']),
    ]
    outputs = [
        ({'a': 1, 'b': '2', 3: 3}, {'a': '1', 'b': '2', '3': '3'}),
    ]
    field = serializers.DictField(child=serializers.CharField())

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            serializers.DictField(child=serializers.CharField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )

    def test_allow_null(self):
        """
        If `allow_null=True` then `None` is a valid input.
        """
        field = serializers.DictField(allow_null=True)
        output = field.run_validation(None)
        assert output is None


class TestNestedDictField(FieldValues):
    """
    Values for nested `DictField` with CharField as child.
    """
    valid_inputs = [
        ({0: {'a': 1, 'b': '2'}, 1: {3: 3}}, {'0': {'a': '1', 'b': '2'}, '1': {'3': '3'}}),
    ]
    invalid_inputs = [
        ({0: {'a': 1, 'b': None}, 1: {'c': None}}, {'0': {'b': ['This field may not be null.']}, '1': {'c': ['This field may not be null.']}}),
        ({0: 'not a dict'}, {'0': ['Expected a dictionary of items but got type "str".']}),
    ]
    outputs = [
        ({0: {'a': 1, 'b': '2'}, 1: {3: 3}}, {'0': {'a': '1', 'b': '2'}, '1': {'3': '3'}}),
    ]
    field = serializers.DictField(child=serializers.DictField(child=serializers.CharField()))


class TestDictFieldWithNullChild(FieldValues):
    """
    Values for `DictField` with allow_null CharField as child.
    """
    valid_inputs = [
        ({'a': None, 'b': '2', 3: 3}, {'a': None, 'b': '2', '3': '3'}),
    ]
    invalid_inputs = [
    ]
    outputs = [
        ({'a': None, 'b': '2', 3: 3}, {'a': None, 'b': '2', '3': '3'}),
    ]
    field = serializers.DictField(child=serializers.CharField(allow_null=True))


class TestUnvalidatedDictField(FieldValues):
    """
    Values for `DictField` with no `child` argument.
    """
    valid_inputs = [
        ({'a': 1, 'b': [4, 5, 6], 1: 123}, {'a': 1, 'b': [4, 5, 6], '1': 123}),
    ]
    invalid_inputs = [
        ('not a dict', ['Expected a dictionary of items but got type "str".']),
    ]
    outputs = [
        ({'a': 1, 'b': [4, 5, 6]}, {'a': 1, 'b': [4, 5, 6]}),
    ]
    field = serializers.DictField()


class TestHStoreField(FieldValues):
    """
    Values for `ListField` with CharField as child.
    """
    valid_inputs = [
        ({'a': 1, 'b': '2', 3: 3}, {'a': '1', 'b': '2', '3': '3'}),
        ({'a': 1, 'b': None}, {'a': '1', 'b': None}),
    ]
    invalid_inputs = [
        ('not a dict', ['Expected a dictionary of items but got type "str".']),
    ]
    outputs = [
        ({'a': 1, 'b': '2', 3: 3}, {'a': '1', 'b': '2', '3': '3'}),
    ]
    field = serializers.HStoreField()

    def test_child_is_charfield(self):
        with pytest.raises(AssertionError) as exc_info:
            serializers.HStoreField(child=serializers.IntegerField())

        assert str(exc_info.value) == (
            "The `child` argument must be an instance of `CharField`, "
            "as the hstore extension stores values as strings."
        )

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            serializers.HStoreField(child=serializers.CharField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )

    def test_allow_null(self):
        """
        If `allow_null=True` then `None` is a valid input.
        """
        field = serializers.HStoreField(allow_null=True)
        output = field.run_validation(None)
        assert output is None


class TestJSONField(FieldValues):
    """
    Values for `JSONField`.
    """
    valid_inputs = [
        ({
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': None
        }, {
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': None
        }),
    ]
    invalid_inputs = [
        ({'a': set()}, ['Value must be valid JSON.']),
        ({'a': float('inf')}, ['Value must be valid JSON.']),
    ]
    outputs = [
        ({
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': 3
        }, {
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': 3
        }),
    ]
    field = serializers.JSONField()

    def test_html_input_as_json_string(self):
        """
        HTML inputs should be treated as a serialized JSON string.
        """
        class TestSerializer(serializers.Serializer):
            config = serializers.JSONField()

        data = QueryDict(mutable=True)
        data.update({'config': '{"a":1}'})
        serializer = TestSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'config': {"a": 1}}


class TestBinaryJSONField(FieldValues):
    """
    Values for `JSONField` with binary=True.
    """
    valid_inputs = [
        (b'{"a": 1, "3": null, "b": ["some", "list", true, 1.23]}', {
            'a': 1,
            'b': ['some', 'list', True, 1.23],
            '3': None
        }),
    ]
    invalid_inputs = [
        ('{"a": "unterminated string}', ['Value must be valid JSON.']),
    ]
    outputs = [
        (['some', 'list', True, 1.23], b'["some", "list", true, 1.23]'),
    ]
    field = serializers.JSONField(binary=True)


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


class TestValidationErrorCode:
    @pytest.mark.parametrize('use_list', (False, True))
    def test_validationerror_code_with_msg(self, use_list):

        class ExampleSerializer(serializers.Serializer):
            password = serializers.CharField()

            def validate_password(self, obj):
                err = DjangoValidationError('exc_msg', code='exc_code')
                if use_list:
                    err = DjangoValidationError([err])
                raise err

        serializer = ExampleSerializer(data={'password': 123})
        serializer.is_valid()
        assert serializer.errors == {'password': ['exc_msg']}
        assert serializer.errors['password'][0].code == 'exc_code'

    @pytest.mark.parametrize('code', (None, 'exc_code',))
    @pytest.mark.parametrize('use_list', (False, True))
    def test_validationerror_code_with_dict(self, use_list, code):

        class ExampleSerializer(serializers.Serializer):

            def validate(self, obj):
                if code is None:
                    err = DjangoValidationError({
                        'email': 'email error',
                    })
                else:
                    err = DjangoValidationError({
                        'email': DjangoValidationError(
                            'email error',
                            code=code),
                    })
                if use_list:
                    err = DjangoValidationError([err])
                raise err

        serializer = ExampleSerializer(data={})
        serializer.is_valid()
        expected_code = code if code else 'invalid'
        if use_list:
            assert serializer.errors == {
                'non_field_errors': [
                    exceptions.ErrorDetail(
                        string='email error',
                        code=expected_code
                    )
                ]
            }
        else:
            assert serializer.errors == {
                'email': ['email error'],
            }
            assert serializer.errors['email'][0].code == expected_code

    @pytest.mark.parametrize('code', (None, 'exc_code',))
    def test_validationerror_code_with_dict_list_same_code(self, code):

        class ExampleSerializer(serializers.Serializer):

            def validate(self, obj):
                if code is None:
                    raise DjangoValidationError({'email': ['email error 1',
                                                           'email error 2']})
                raise DjangoValidationError({'email': [
                    DjangoValidationError('email error 1', code=code),
                    DjangoValidationError('email error 2', code=code),
                ]})

        serializer = ExampleSerializer(data={})
        serializer.is_valid()
        expected_code = code if code else 'invalid'
        assert serializer.errors == {
            'email': [
                exceptions.ErrorDetail(
                    string='email error 1',
                    code=expected_code
                ),
                exceptions.ErrorDetail(
                    string='email error 2',
                    code=expected_code
                ),
            ]
        }
