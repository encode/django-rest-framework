import pytest
from django.contrib.admin import site
from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework.authtoken.admin import TokenAdmin
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
