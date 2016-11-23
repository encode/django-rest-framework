from django.test import TestCase

from rest_framework import serializers


class WriteOnlyFieldTests(TestCase):
    def setUp(self):
        class ExampleSerializer(serializers.Serializer):
            email = serializers.EmailField()
            password = serializers.CharField(write_only=True)

            def create(self, attrs):
                return attrs

        self.Serializer = ExampleSerializer

    def write_only_fields_are_present_on_input(self):
        data = {
            'email': 'foo@example.com',
            'password': '123'
        }
        serializer = self.Serializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == data

    def write_only_fields_are_not_present_on_output(self):
        instance = {
            'email': 'foo@example.com',
            'password': '123'
        }
        serializer = self.Serializer(instance)
        assert serializer.data == {'email': 'foo@example.com'}
