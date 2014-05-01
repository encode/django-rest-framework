from rest_framework import serializers

from tests.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
