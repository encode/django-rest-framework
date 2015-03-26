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
        class PaymentInfoSerializer(serializers.Serializer):
            url = serializers.URLField()
            amount = serializers.DecimalField(max_digits=6, decimal_places=2)

        class NestedSerializer(serializers.Serializer):
            foo = serializers.CharField()

        class AcceptRequestSerializer(serializers.Serializer):
            ERROR_MESSAGE = '`payment_info` is required under this condition'

            nested = NestedSerializer(many=True)
            payment_info = PaymentInfoSerializer(many=True, allow_null=True)

            def validate_payment_info(self, value):
                if value is None and not self.context['condition_to_allow_null']:
                    raise serializers.ValidationError(self.ERROR_MESSAGE)

                return value

        self.Serializer = AcceptRequestSerializer

    def get_serializer(self, data, condition_to_allow_null=True):
        return self.Serializer(
            data=data,
            context={'condition_to_allow_null': condition_to_allow_null})

    def test_null_allowed_if_allow_null_is_set(self):
        input_data = {
            'nested': [{'foo': 'bar'}],
            'payment_info': None
        }
        expected_data = {
            'nested': [{'foo': 'bar'}],
            'payment_info': None
        }
        serializer = self.get_serializer(input_data)

        assert serializer.is_valid(), serializer.errors
        assert serializer.validated_data == expected_data

    def test_null_is_not_allowed_if_allow_null_is_not_set(self):
        input_data = {
            'nested': None,
            'payment_info': None
        }
        serializer = self.get_serializer(input_data)

        assert not serializer.is_valid()
        assert set(serializer.errors) == set(['nested'])
        assert serializer.errors['nested'][0] == serializer.error_messages['null']

    def test_run_the_field_validation_even_if_the_field_is_null(self):
        input_data = {
            'nested': [{'foo': 'bar'}],
            'payment_info': None,
        }
        serializer = self.get_serializer(input_data, condition_to_allow_null=False)

        assert not serializer.is_valid()
        assert set(serializer.errors) == set(['payment_info'])
        assert serializer.errors['payment_info'][0] == serializer.ERROR_MESSAGE

    def test_expected_results_if_not_null(self):
        input_data = {
            'nested': [{'foo': 'bar'}],
            'payment_info': [
                {'url': 'https://domain.org/api/payment-method/1/', 'amount': '22'},
                {'url': 'https://domain.org/api/payment-method/2/', 'amount': '33'},
            ]
        }
        expected_data = {
            'nested': [{'foo': 'bar'}],
            'payment_info': [
                {'url': 'https://domain.org/api/payment-method/1/', 'amount': 22},
                {'url': 'https://domain.org/api/payment-method/2/', 'amount': 33},
            ]
        }
        serializer = self.get_serializer(input_data)

        assert serializer.is_valid()
        assert serializer.validated_data == expected_data
