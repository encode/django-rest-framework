from django.db import models
from rest_framework import serializers
from rest_framework.validators import (
    UniqueTogetherValidator,
)

from rest_framework import viewsets
import json
from rest_framework import mixins
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.test import TestCase
from rest_framework import status


class ModelTwo(models.Model):
    testfieldtwo = models.CharField(max_length=60, primary_key=True)

class ModelOne(models.Model):
    testfield = models.ForeignKey(ModelTwo, on_delete=models.CASCADE)
    alias = models.CharField(max_length=60)
    name = models.CharField(max_length=60)

    class Meta:
        unique_together = ('testfield', 'name',)


class ExampleSerializer(serializers.ModelSerializer):
    altername = serializers.CharField(source="testfield", default=ModelTwo(testfieldtwo="model 2 default"), read_only=True)
    
    class Meta:
        model = ModelOne
        fields = ('altername' ,'alias', 'name')
        validators = [
            UniqueTogetherValidator(
                queryset=ModelOne.objects.all(),
                fields=('testfield', 'name')
            )
        ]

class ExampleViewSet(mixins.CreateModelMixin,
                             mixins.UpdateModelMixin,
                             viewsets.ReadOnlyModelViewSet):

    queryset = ModelOne.objects.all()
    serializer_class = ExampleSerializer


class ExampleTests(TestCase):

    def url(self):
        return '/example/'
    
    def test_created_successfully(self):
        name = 'blab blah'
        alias = 'ab ab'
        response = self.client.post(self.url, {'name': name, 'alias': alias})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
