import uuid

import pytest
from django.http import QueryDict

from rest_framework import serializers


class TestInvalidErrorKey:
    def setup(self):
        class ExampleField(serializers.Field):
            def to_representation(self, value):
                self.fail('incorrect')
        self.field = ExampleField()

    def test_invalid_error_key(self):
        """
        If a field raises a validation error, but does not have a corresponding
        error message, then raise an appropriate assertion error.
        """
        with pytest.raises(AssertionError) as exc_info:
            self.field.to_representation(123)
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
        assert list(serializer.validated_data.keys()) == ['message']

    def test_empty_html_uuidfield_with_optional(self):
        class TestSerializer(serializers.Serializer):
            message = serializers.UUIDField(required=False)

        serializer = TestSerializer(data=QueryDict('message='))
        assert serializer.is_valid()
        assert list(serializer.validated_data.keys()) == []

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
