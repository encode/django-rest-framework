from rest_framework import generics
from rest_framework.tests.models import NullableForeignKeySource
from rest_framework.tests.serializers import NullableFKSourceSerializer


class NullableFKSourceDetail(generics.RetrieveUpdateDestroyAPIView):
    model = NullableForeignKeySource
    model_serializer_class = NullableFKSourceSerializer
