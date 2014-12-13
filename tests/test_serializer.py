from __future__ import unicode_literals
from rest_framework import serializers
import pytest


# Tests for core functionality.
# -----------------------------

class TestSerializer:
    def setup(self):
        class ExampleSerializer(serializers.Serializer):
            char = serializers.CharField()
            integer = serializers.IntegerField()
        self.Serializer = ExampleSerializer

    def test_valid_serializer(self):
        serializer = self.Serializer(data={'char': 'abc', 'integer': 123})
        assert serializer.is_valid()
        assert serializer.validated_data == {'char': 'abc', 'integer': 123}
        assert serializer.errors == {}

    def test_invalid_serializer(self):
        serializer = self.Serializer(data={'char': 'abc'})
        assert not serializer.is_valid()
        assert serializer.validated_data == {}
        assert serializer.errors == {'integer': ['This field is required.']}

    def test_partial_validation(self):
        serializer = self.Serializer(data={'char': 'abc'}, partial=True)
        assert serializer.is_valid()
        assert serializer.validated_data == {'char': 'abc'}
        assert serializer.errors == {}

    def test_empty_serializer(self):
        serializer = self.Serializer()
        assert serializer.data == {'char': '', 'integer': None}

    def test_missing_attribute_during_serialization(self):
        class MissingAttributes:
            pass
        instance = MissingAttributes()
        serializer = self.Serializer(instance)
        with pytest.raises(AttributeError):
            serializer.data


class TestValidateMethod:
    def test_non_field_error_validate_method(self):
        class ExampleSerializer(serializers.Serializer):
            char = serializers.CharField()
            integer = serializers.IntegerField()

            def validate(self, attrs):
                raise serializers.ValidationError('Non field error')

        serializer = ExampleSerializer(data={'char': 'abc', 'integer': 123})
        assert not serializer.is_valid()
        assert serializer.errors == {'non_field_errors': ['Non field error']}

    def test_field_error_validate_method(self):
        class ExampleSerializer(serializers.Serializer):
            char = serializers.CharField()
            integer = serializers.IntegerField()

            def validate(self, attrs):
                raise serializers.ValidationError({'char': 'Field error'})

        serializer = ExampleSerializer(data={'char': 'abc', 'integer': 123})
        assert not serializer.is_valid()
        assert serializer.errors == {'char': ['Field error']}


class TestBaseSerializer:
    def setup(self):
        class ExampleSerializer(serializers.BaseSerializer):
            def to_representation(self, obj):
                return {
                    'id': obj['id'],
                    'email': obj['name'] + '@' + obj['domain']
                }

            def to_internal_value(self, data):
                name, domain = str(data['email']).split('@')
                return {
                    'id': int(data['id']),
                    'name': name,
                    'domain': domain,
                }

        self.Serializer = ExampleSerializer

    def test_serialize_instance(self):
        instance = {'id': 1, 'name': 'tom', 'domain': 'example.com'}
        serializer = self.Serializer(instance)
        assert serializer.data == {'id': 1, 'email': 'tom@example.com'}

    def test_serialize_list(self):
        instances = [
            {'id': 1, 'name': 'tom', 'domain': 'example.com'},
            {'id': 2, 'name': 'ann', 'domain': 'example.com'},
        ]
        serializer = self.Serializer(instances, many=True)
        assert serializer.data == [
            {'id': 1, 'email': 'tom@example.com'},
            {'id': 2, 'email': 'ann@example.com'}
        ]

    def test_validate_data(self):
        data = {'id': 1, 'email': 'tom@example.com'}
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'id': 1,
            'name': 'tom',
            'domain': 'example.com'
        }

    def test_validate_list(self):
        data = [
            {'id': 1, 'email': 'tom@example.com'},
            {'id': 2, 'email': 'ann@example.com'},
        ]
        serializer = self.Serializer(data=data, many=True)
        assert serializer.is_valid()
        assert serializer.validated_data == [
            {'id': 1, 'name': 'tom', 'domain': 'example.com'},
            {'id': 2, 'name': 'ann', 'domain': 'example.com'}
        ]


class TestStarredSource:
    """
    Tests for `source='*'` argument, which is used for nested representations.

    For example:

        nested_field = NestedField(source='*')
    """
    data = {
        'nested1': {'a': 1, 'b': 2},
        'nested2': {'c': 3, 'd': 4}
    }

    def setup(self):
        class NestedSerializer1(serializers.Serializer):
            a = serializers.IntegerField()
            b = serializers.IntegerField()

        class NestedSerializer2(serializers.Serializer):
            c = serializers.IntegerField()
            d = serializers.IntegerField()

        class TestSerializer(serializers.Serializer):
            nested1 = NestedSerializer1(source='*')
            nested2 = NestedSerializer2(source='*')

        self.Serializer = TestSerializer

    def test_nested_validate(self):
        """
        A nested representation is validated into a flat internal object.
        """
        serializer = self.Serializer(data=self.data)
        assert serializer.is_valid()
        assert serializer.validated_data == {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4
        }

    def test_nested_serialize(self):
        """
        An object can be serialized into a nested representation.
        """
        instance = {'a': 1, 'b': 2, 'c': 3, 'd': 4}
        serializer = self.Serializer(instance)
        assert serializer.data == self.data


class TestIncorrectlyConfigured:
    def test_incorrect_field_name(self):
        class ExampleSerializer(serializers.Serializer):
            incorrect_name = serializers.IntegerField()

        class ExampleObject:
            def __init__(self):
                self.correct_name = 123

        instance = ExampleObject()
        serializer = ExampleSerializer(instance)
        with pytest.raises(AttributeError) as exc_info:
            serializer.data
        assert str(exc_info.value) == (
            "Got AttributeError when attempting to get a value for field `incorrect_name` on serializer `ExampleSerializer`.\n"
            "The serializer field might be named incorrectly and not match any attribute or key on the `ExampleObject` instance.\n"
            "Original exception text was: ExampleObject instance has no attribute 'incorrect_name'."
        )
