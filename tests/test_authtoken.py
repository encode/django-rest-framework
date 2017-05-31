import pytest
from django.contrib.admin import site
from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.management.commands.drf_create_token import \
    Command as AuthTokenCommand
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError


class AuthTokenTests(TestCase):

    def setUp(self):
        self.site = site
        self.user = User.objects.create_user(username='test_user')
        self.token = Token.objects.create(key='test token', user=self.user)

    def test_model_admin_displayed_fields(self):
        mock_request = object()
        token_admin = TokenAdmin(self.token, self.site)
        assert token_admin.get_fields(mock_request) == ('user',)

    def test_token_string_representation(self):
        assert str(self.token) == 'test token'

    def test_validate_raise_error_if_no_credentials_provided(self):
        with pytest.raises(ValidationError):
            AuthTokenSerializer().validate({})

    def test_whitespace_in_password(self):
        data = {'username': self.user.username, 'password': 'test pass '}
        self.user.set_password(data['password'])
        self.user.save()
        assert AuthTokenSerializer(data=data).is_valid()


class AuthTokenCommandTests(TestCase):

    def setUp(self):
        self.site = site
        self.user = User.objects.create_user(username='test_user')

    def test_command_create_user_token(self):
        token = AuthTokenCommand().create_user_token(self.user.username)
        assert token is not None
        token_saved = Token.objects.first()
        assert token.key == token_saved.key

    def test_command_create_user_token_invalid_user(self):
        with pytest.raises(User.DoesNotExist):
            AuthTokenCommand().create_user_token('not_existing_user')
