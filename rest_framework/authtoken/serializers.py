from django.contrib.auth import authenticate, get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(
        label=_("Username"),
        write_only=True
    )
    password = serializers.CharField(
        label=_("Password"),
        style={'input_type': 'password'},
        trim_whitespace=False,
        write_only=True
    )
    token = serializers.CharField(
        label=_("Token"),
        read_only=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        username_field = User.USERNAME_FIELD
        if username_field != 'username' and 'username' in self.fields:
            # Rebuild the fields mapping to preserve the original position
            # of the login field when renaming it.
            original_items = list(self.fields.items())
            new_fields = self.fields.__class__(self)
            for name, field in original_items:
                if name == 'username':
                    name = username_field
                    field.label = _(username_field.capitalize())
                new_fields[name] = field
            self.fields = new_fields

    def validate(self, attrs):
        User = get_user_model()
        username_field = User.USERNAME_FIELD
        username = attrs.get(username_field)
        password = attrs.get('password')

        if username and password:
            user = authenticate(
                request=self.context.get('request'),
                **{username_field: username, 'password': password}
            )

            # The authenticate call simply returns None for is_active=False
            # users. (Assuming the default ModelBackend authentication
            # backend.)
            if not user:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg, code='authorization')
        else:
            msg = _(f'Must include "{username_field}" and "password".')
            raise serializers.ValidationError(msg, code='authorization')

        attrs['user'] = user
        return attrs
