from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.authtoken.models import Token


class AuthTokenSerializer(serializers.Serializer):
    token = serializers.Field(source="key")
    username = serializers.CharField(max_length=30)
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)

            if user:
                if not user.is_active:
                    raise serializers.ValidationError('User account is disabled.')
                attrs['user'] = user
                return attrs
            else:
                raise serializers.ValidationError('Unable to login with provided credentials.')
        else:
            raise serializers.ValidationError('Must include "username" and "password"')

    def convert_object(self, obj):
        ret = self._dict_class()
        ret['token'] = obj.key
        ret['user'] = obj.user.id
        return ret

    def restore_object(self, attrs, instance=None):
        token, created = Token.objects.get_or_create(user=attrs['user'])
        return token
