from rest_framework import serializers

from rest_framework.tests.accounts.models import Account
from rest_framework.tests.users.serializers import UserSerializer


class AccountSerializer(serializers.ModelSerializer):
    admins = UserSerializer(many=True)

    class Meta:
        model = Account
