from django.db import models
from django.test import TestCase
from rest_framework import serializers


class ExampleModel(models.Model):
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=100)


class WriteOnlyFieldTests(TestCase):
    def test_write_only_fields(self):
        class ExampleSerializer(serializers.Serializer):
            email = serializers.EmailField()
            password = serializers.CharField(write_only=True)

        data = {
            'email': 'foo@example.com',
            'password': '123'
        }
        serializer = ExampleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.object, data)
        self.assertEquals(serializer.data, {'email': 'foo@example.com'})

    def test_write_only_fields_meta(self):
        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = ExampleModel
                fields = ('email', 'password')
                write_only_fields = ('password',)

        data = {
            'email': 'foo@example.com',
            'password': '123'
        }
        serializer = ExampleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(isinstance(serializer.object, ExampleModel))
        self.assertEquals(serializer.object.email, data['email'])
        self.assertEquals(serializer.object.password, data['password'])
        self.assertEquals(serializer.data, {'email': 'foo@example.com'})
