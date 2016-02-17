from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(label=_("Username"))
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)

            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    code = 'authorization'
                    raise serializers.ValidationError(msg, code=code)
            else:
                msg = _('Unable to log in with provided credentials.')
                code = 'authorization'
                raise serializers.ValidationError(msg, code=code)

        else:
            msg = _('Must include "username" and "password".')
            code = 'authorization'
            raise serializers.ValidationError(msg, code=code)

        attrs['user'] = user
        return attrs
