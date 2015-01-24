from __future__ import unicode_literals

from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework import authentication
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.versioning import NamespaceVersioning
from .models import Foo, Bar
from .serializers import FooSerializer, BarSerializer


class MockView(APIView):

    authentication_classes = (authentication.SessionAuthentication,)
    renderer_classes = (renderers.BrowsableAPIRenderer,)

    def get(self, request):
        return Response({'a': 1, 'b': 2, 'c': 3})


class SerializerClassMixin(object):
    def get_serializer_class(self):
        # Get base name of serializer
        self.request.version
        return self.serializer_class


class FooViewSet(SerializerClassMixin, ModelViewSet):
    versioning_class = NamespaceVersioning
    model = Foo
    queryset = Foo.objects.all()
    serializer_class = FooSerializer
    renderer_classes = (BrowsableAPIRenderer, JSONRenderer)


class BarViewSet(SerializerClassMixin, ModelViewSet):
    model = Bar
    queryset = Bar.objects.all()
    serializer_class = BarSerializer
    renderer_classes = (BrowsableAPIRenderer, )
