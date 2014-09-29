from django.db import models
from django.test import TestCase
from rest_framework import serializers


class ExampleModel(models.Model):
    username = models.CharField(unique=True, max_length=100)


class ExampleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExampleModel


class TestUniquenessValidation(TestCase):
    def setUp(self):
        self.instance = ExampleModel.objects.create(username='existing')

    def test_is_not_unique(self):
        data = {'username': 'existing'}
        serializer = ExampleSerializer(data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'username': ['This field must be unique.']}

    def test_is_unique(self):
        data = {'username': 'other'}
        serializer = ExampleSerializer(data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'username': 'other'}

    def test_updated_instance_excluded(self):
        data = {'username': 'existing'}
        serializer = ExampleSerializer(self.instance, data=data)
        assert serializer.is_valid()
        assert serializer.validated_data == {'username': 'existing'}
