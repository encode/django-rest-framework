from rest_framework import serializers

from rest_framework.tests.users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
