from rest_framework import serializers

from rest_framework.tests.models import NullableForeignKeySource


class NullableFKSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NullableForeignKeySource
