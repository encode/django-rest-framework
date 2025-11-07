from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

USER_MODEL = get_user_model()


class AuthTokenSerializer(serializers.Serializer):
    def __init__(self, instance=None, data=None, **kwargs):
        super().__init__(instance, data=data, **kwargs)
        self.identifier_fiend_name = USER_MODEL.USERNAME_FIELD
        if USER_MODEL.get_email_field_name() == self.identifier_fiend_name:
            self.fields[self.identifier_fiend_name] = serializers.EmailField(
                label=_(self.identifier_fiend_name.title()),
                write_only=True
            )
        else:
            self.fields[self.identifier_fiend_name] = serializers.CharField(
                label=_(self.identifier_fiend_name.title()),
                write_only=True
            )
        self.fields["password"] = serializers.CharField(
            label=_("Password"),
            style={'input_type': 'password'},
            trim_whitespace=False,
            write_only=True
        )

    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def validate(self, attrs):
        identifier_value = attrs.get(self.identifier_fiend_name)
        password = attrs.get('password')

        if identifier_value and password:
            credentials = {
                self.identifier_fiend_name: identifier_value,
                "password": password,
            }
            user = authenticate(
                request=self.context.get('request'),
                **credentials,
            )

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _(f'Must include "{self.identifier_fiend_name}" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
