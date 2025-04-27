import pytest
from django.db import models
from django.http import QueryDict
from django.test import TestCase

from rest_framework import serializers
from rest_framework.compat import postgres_fields
from rest_framework.serializers import raise_errors_on_nested_writes


class TestNestedSerializer:
    def setup_method(self):
        class NestedSerializer(serializers.Serializer):
            one = serializers.IntegerField(max_value=10)
            two = serializers.IntegerField(max_value=10)

        class TestSerializer(serializers.Serializer):
            nested = NestedSerializer()

        self.Serializer = TestSerializer

    def test_nested_validate(self):
        input_data = {
            'nested': {
                'one': '1',
                'two': '2',
            }
        }
        expected_data = {
            'nested': {
                'one': 1,
                'two': 2,
            }
        }
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert serializer.validated_data == expected_data

    def test_nested_serialize_empty(self):
        expected_data = {
            'nested': {
                'one': None,
                'two': None
            }
        }
        serializer = self.Serializer()
        assert serializer.data == expected_data

    def test_nested_serialize_no_data(self):
        data = None
        serializer = self.Serializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'non_field_errors': ['No data provided']}


class TestNotRequiredNestedSerializer:
    def setup_method(self):
        class NestedSerializer(serializers.Serializer):
            one = serializers.IntegerField(max_value=10)

        class TestSerializer(serializers.Serializer):
            nested = NestedSerializer(required=False)

        self.Serializer = TestSerializer

    def test_json_validate(self):
        input_data = {}
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()

        input_data = {'nested': {'one': '1'}}
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()

    def test_multipart_validate(self):
        input_data = QueryDict('')
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()

        input_data = QueryDict('nested[one]=1')
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()


class TestNestedSerializerWithMany:
    def setup_method(self):
        class NestedSerializer(serializers.Serializer):
            example = serializers.IntegerField(max_value=10)

        class TestSerializer(serializers.Serializer):
            allow_null = NestedSerializer(many=True, allow_null=True)
            not_allow_null = NestedSerializer(many=True)
            allow_empty = NestedSerializer(many=True, allow_empty=True)
            not_allow_empty = NestedSerializer(many=True, allow_empty=False)

        self.Serializer = TestSerializer

    def test_null_allowed_if_allow_null_is_set(self):
        input_data = {
            'allow_null': None,
            'not_allow_null': [{'example': '2'}, {'example': '3'}],
            'allow_empty': [{'example': '2'}],
            'not_allow_empty': [{'example': '2'}],
        }
        expected_data = {
            'allow_null': None,
            'not_allow_null': [{'example': 2}, {'example': 3}],
            'allow_empty': [{'example': 2}],
            'not_allow_empty': [{'example': 2}],
        }
        serializer = self.Serializer(data=input_data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == expected_data

    def test_null_is_not_allowed_if_allow_null_is_not_set(self):
        input_data = {
            'allow_null': None,
            'not_allow_null': None,
            'allow_empty': [{'example': '2'}],
            'not_allow_empty': [{'example': '2'}],
        }
        serializer = self.Serializer(data=input_data)

        assert not serializer.is_valid()

        expected_errors = {'not_allow_null': [serializer.error_messages['null']]}
        assert serializer.errors == expected_errors

    def test_run_the_field_validation_even_if_the_field_is_null(self):
        class TestSerializer(self.Serializer):
            validation_was_run = False

            def validate_allow_null(self, value):
                TestSerializer.validation_was_run = True
                return value

        input_data = {
            'allow_null': None,
            'not_allow_null': [{'example': 2}],
            'allow_empty': [{'example': 2}],
            'not_allow_empty': [{'example': 2}],
        }
        serializer = TestSerializer(data=input_data)

        assert serializer.is_valid()
        assert serializer.validated_data == input_data
        assert TestSerializer.validation_was_run

    def test_empty_allowed_if_allow_empty_is_set(self):
        input_data = {
            'allow_null': [{'example': '2'}],
            'not_allow_null': [{'example': '2'}],
            'allow_empty': [],
            'not_allow_empty': [{'example': '2'}],
        }
        expected_data = {
            'allow_null': [{'example': 2}],
            'not_allow_null': [{'example': 2}],
            'allow_empty': [],
            'not_allow_empty': [{'example': 2}],
        }
        serializer = self.Serializer(data=input_data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == expected_data

    def test_empty_not_allowed_if_allow_empty_is_set_to_false(self):
        input_data = {
            'allow_null': [{'example': '2'}],
            'not_allow_null': [{'example': '2'}],
            'allow_empty': [],
            'not_allow_empty': [],
        }
        serializer = self.Serializer(data=input_data)

        assert not serializer.is_valid()

        expected_errors = {'not_allow_empty': {'non_field_errors': [serializers.ListSerializer.default_error_messages['empty']]}}
        assert serializer.errors == expected_errors


class TestNestedSerializerWithList:
    def setup_method(self):
        class NestedSerializer(serializers.Serializer):
            example = serializers.MultipleChoiceField(choices=[1, 2, 3])

        class TestSerializer(serializers.Serializer):
            nested = NestedSerializer()

        self.Serializer = TestSerializer

    def test_nested_serializer_with_list_json(self):
        input_data = {
            'nested': {
                'example': [1, 2],
            }
        }
        serializer = self.Serializer(data=input_data)

        assert serializer.is_valid()
        assert serializer.validated_data['nested']['example'] == {1, 2}

    def test_nested_serializer_with_list_multipart(self):
        input_data = QueryDict('nested.example=1&nested.example=2')
        serializer = self.Serializer(data=input_data)

        assert serializer.is_valid()
        assert serializer.validated_data['nested']['example'] == {1, 2}


class TestNotRequiredNestedSerializerWithMany:
    def setup_method(self):
        class NestedSerializer(serializers.Serializer):
            one = serializers.IntegerField(max_value=10)

        class TestSerializer(serializers.Serializer):
            nested = NestedSerializer(required=False, many=True)

        self.Serializer = TestSerializer

    def test_json_validate(self):
        input_data = {}
        serializer = self.Serializer(data=input_data)

        # request is empty, therefore 'nested' should not be in serializer.data
        assert serializer.is_valid()
        assert 'nested' not in serializer.validated_data

        input_data = {'nested': [{'one': '1'}, {'one': 2}]}
        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert 'nested' in serializer.validated_data

    def test_multipart_validate(self):
        # leave querydict empty
        input_data = QueryDict('')
        serializer = self.Serializer(data=input_data)

        # the querydict is empty, therefore 'nested' should not be in serializer.data
        assert serializer.is_valid()
        assert 'nested' not in serializer.validated_data

        input_data = QueryDict('nested[0]one=1&nested[1]one=2')

        serializer = self.Serializer(data=input_data)
        assert serializer.is_valid()
        assert 'nested' in serializer.validated_data


class NestedWriteProfile(models.Model):
    address = models.CharField(max_length=100)


class NestedWritePerson(models.Model):
    profile = models.ForeignKey(NestedWriteProfile, on_delete=models.CASCADE)


class TestNestedWriteErrors(TestCase):
    # tests for rests_framework.serializers.raise_errors_on_nested_writes
    def test_nested_serializer_error(self):
        class ProfileSerializer(serializers.ModelSerializer):
            class Meta:
                model = NestedWriteProfile
                fields = ['address']

        class NestedProfileSerializer(serializers.ModelSerializer):
            profile = ProfileSerializer()

            class Meta:
                model = NestedWritePerson
                fields = ['profile']

        serializer = NestedProfileSerializer(data={'profile': {'address': '52 festive road'}})
        assert serializer.is_valid()
        assert serializer.validated_data == {'profile': {'address': '52 festive road'}}
        with pytest.raises(AssertionError) as exc_info:
            serializer.save()

        assert str(exc_info.value) == (
            'The `.create()` method does not support writable nested fields by '
            'default.\nWrite an explicit `.create()` method for serializer '
            '`tests.test_serializer_nested.NestedProfileSerializer`, or set '
            '`read_only=True` on nested serializer fields.'
        )

    def test_dotted_source_field_error(self):
        class DottedAddressSerializer(serializers.ModelSerializer):
            address = serializers.CharField(source='profile.address')

            class Meta:
                model = NestedWritePerson
                fields = ['address']

        serializer = DottedAddressSerializer(data={'address': '52 festive road'})
        assert serializer.is_valid()
        assert serializer.validated_data == {'profile': {'address': '52 festive road'}}
        with pytest.raises(AssertionError) as exc_info:
            serializer.save()

        assert str(exc_info.value) == (
            'The `.create()` method does not support writable dotted-source '
            'fields by default.\nWrite an explicit `.create()` method for '
            'serializer `tests.test_serializer_nested.DottedAddressSerializer`, '
            'or set `read_only=True` on dotted-source serializer fields.'
        )


if postgres_fields:
    class NonRelationalPersonModel(models.Model):
        """Model declaring a postgres JSONField"""
        data = postgres_fields.JSONField()

        class Meta:
            required_db_features = {'supports_json_field'}


@pytest.mark.skipif(not postgres_fields, reason='psycopg2 is not installed')
class TestNestedNonRelationalFieldWrite:
    """
    Test that raise_errors_on_nested_writes does not raise `AssertionError` when the
    model field is not a relation.
    """

    def test_nested_serializer_create_and_update(self):

        class NonRelationalPersonDataSerializer(serializers.Serializer):
            occupation = serializers.CharField()

        class NonRelationalPersonSerializer(serializers.ModelSerializer):
            data = NonRelationalPersonDataSerializer()

            class Meta:
                model = NonRelationalPersonModel
                fields = ['data']

        serializer = NonRelationalPersonSerializer(data={'data': {'occupation': 'developer'}})
        assert serializer.is_valid()
        assert serializer.validated_data == {'data': {'occupation': 'developer'}}
        raise_errors_on_nested_writes('create', serializer, serializer.validated_data)
        raise_errors_on_nested_writes('update', serializer, serializer.validated_data)

    def test_dotted_source_field_create_and_update(self):

        class DottedNonRelationalPersonSerializer(serializers.ModelSerializer):
            occupation = serializers.CharField(source='data.occupation')

            class Meta:
                model = NonRelationalPersonModel
                fields = ['occupation']

        serializer = DottedNonRelationalPersonSerializer(data={'occupation': 'developer'})
        assert serializer.is_valid()
        assert serializer.validated_data == {'data': {'occupation': 'developer'}}
        raise_errors_on_nested_writes('create', serializer, serializer.validated_data)
        raise_errors_on_nested_writes('update', serializer, serializer.validated_data)
