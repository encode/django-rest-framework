from django.db import models
from rest_framework import serializers, viewsets
from rest_framework.decorators import detail_route


class DummyModel(models.Model):
    pass


class DummySerializer(serializers.ModelSerializer):

    class Meta:
        model = DummyModel
        fields = ('id', )


class DummyViewSet(viewsets.ModelViewSet):
    serializer_class = DummySerializer
    queryset = DummyModel.objects.all()

    @detail_route(methods=['get', 'post'])
    def retrieve_alt(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
