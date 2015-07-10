from django.contrib.auth import authenticate
from django.utils.translation import ugettext_lazy as _

from rest_framework import exceptions, serializers


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(style={'input_type': 'password'})

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)

            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise exceptions.ValidationError(
                        msg,
                        error_code='authorization'
                    )
            else:
                msg = _('Unable to log in with provided credentials.')
                raise exceptions.ValidationError(
                    msg,
                    error_code='authorization'
                )
        else:
            msg = _('Must include "username" and "password".')
            raise exceptions.ValidationError(
                msg,
                error_code='authorization'
            )

        attrs['user'] = user
        return attrs
