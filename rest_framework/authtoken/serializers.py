from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers
from rest_framework.fields import empty


class AuthTokenSerializer(serializers.Serializer):
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})

    def __init__(self, data=empty, **kwargs):
        self.fields[get_user_model().USERNAME_FIELD] = serializers.CharField(label=_(get_user_model().USERNAME_FIELD))
        super(self.__class__, self).__init__(self, data, **kwargs)

    def validate(self, attrs):
        username = attrs.get('%s' % get_user_model().USERNAME_FIELD)
        password = attrs.get('password')

        if username and password:
            user = authenticate(**{'%s' % get_user_model().USERNAME_FIELD: username, 'password': password})

            if user:
                if not user.is_active:
                    msg = _('User account is disabled.')
                    raise serializers.ValidationError(msg)
            else:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "%s" and "password".' % get_user_model().USERNAME_FIELD)
            raise serializers.ValidationError(msg)

        attrs['user'] = user
        return attrs
