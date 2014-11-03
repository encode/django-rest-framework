from __future__ import unicode_literals

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework import renderers
from rest_framework import generics
from rest_framework import serializers
from rest_framework.response import Response

from tests.models import BasicModel


class MockView(APIView):

    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer,)

    def get(self, request):
        return Response({'a': 1, 'b': 2, 'c': 3})


class CreateOnlySerializer(serializers.ModelSerializer):
    def restore_object(self, attrs, instance=None):
        assert instance is None, 'Cannot update models with this serializer'
        return super(CreateOnlySerializer, self).restore_object(attrs, instance=instance)

    class Meta:
        model = BasicModel


class CreateOnlyView(generics.ListCreateAPIView):
    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer,)
    serializer_class = CreateOnlySerializer
    model = BasicModel
