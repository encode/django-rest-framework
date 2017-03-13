from django.db import models
from rest_framework import serializers, viewsets


class DummyModel(models.Model):
    pass


class DummySerializer(serializers.ModelSerializer):

    class Meta:
        model = DummyModel
        fields = ('id', )


class DummyViewSet(viewsets.ModelViewSet):
    serializer_class = DummySerializer
    queryset = DummyModel.objects.all()
