from rest_framework import serializers
from tests.models import NullableForeignKeySource


class NullableFKSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NullableForeignKeySource
