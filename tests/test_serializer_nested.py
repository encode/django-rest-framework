from django.http import QueryDict

from rest_framework import serializers


class TestNestedSerializer:
    def setup(self):
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
    def setup(self):
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
    def setup(self):
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
    def setup(self):
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
        assert serializer.validated_data['nested']['example'] == set([1, 2])

    def test_nested_serializer_with_list_multipart(self):
        input_data = QueryDict('nested.example=1&nested.example=2')
        serializer = self.Serializer(data=input_data)

        assert serializer.is_valid()
        assert serializer.validated_data['nested']['example'] == set([1, 2])
