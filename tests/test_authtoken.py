import importlib
from io import StringIO
from unittest import mock

import pytest
from django.contrib.admin import site
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.db import IntegrityError
from django.test import TestCase, modify_settings

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

    def test_authtoken_can_be_imported_when_not_included_in_installed_apps(self):
        import rest_framework.authtoken.models
        with modify_settings(INSTALLED_APPS={'remove': 'rest_framework.authtoken'}):
            importlib.reload(rest_framework.authtoken.models)
        # Set the proxy and abstract properties back to the version,
        # where authtoken is among INSTALLED_APPS.
        importlib.reload(rest_framework.authtoken.models)

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



    def test_token_creation_collision_raises_integrity_error(self):
        """
        Verify that creating a token with an existing key raises IntegrityError.
        """
        user2 = User.objects.create_user('user2', 'user2@example.com', 'p')
        existing_token = Token.objects.create(user=user2)

        # Try to create another token with the same key
        with self.assertRaises(IntegrityError):
            Token.objects.create(key=existing_token.key, user=self.user)

    def test_key_regeneration_on_save_is_not_a_breaking_change(self):
        """
        Verify that when a token is created without a key, it generates one correctly.
        This tests the backward compatibility scenario where existing code might
        create tokens without explicitly setting a key.
        """
        # Create a new user for this test to avoid conflicts with setUp token
        user2 = User.objects.create_user('test_user2', 'test2@example.com', 'password')
        
        # Create a token without a key - it should generate one automatically
        token = Token(user=user2)
        token.key = ""  # Explicitly clear the key
        token.save()

        # Verify the key was generated
        self.assertEqual(len(token.key), 40)
        self.assertEqual(token.user, user2)

        # Verify it's saved in the database
        token.refresh_from_db()
        self.assertEqual(len(token.key), 40)
        self.assertEqual(token.user, user2)

    def test_saving_existing_token_without_changes_does_not_alter_key(self):
        """
        Ensure that calling save() on an existing token without modifications
        does not change its key.
        """
        original_key = self.token.key

        self.token.save()
        self.assertEqual(self.token.key, original_key)

    def test_generate_key_uses_os_urandom(self):
        """
        Verify that `generate_key` correctly calls `os.urandom`.
        """
        with mock.patch('rest_framework.authtoken.models.os.urandom') as mock_urandom:
            mock_urandom.return_value = b'a_mocked_key_of_proper_length_0123456789'
            key = Token.generate_key()

            mock_urandom.assert_called_once_with(20)
            self.assertEqual(key, '615f6d6f636b65645f6b65795f6f665f70726f7065725f6c656e6774685f30313233343536373839')


class AuthTokenCommandTests(TestCase):

    def setUp(self):
        self.site = site
        self.user = User.objects.create_user(username='test_user')

    def test_command_create_user_token(self):
        token = AuthTokenCommand().create_user_token(self.user.username, False)
        assert token is not None
        token_saved = Token.objects.first()
        assert token.key == token_saved.key

    def test_command_create_user_token_invalid_user(self):
        with pytest.raises(User.DoesNotExist):
            AuthTokenCommand().create_user_token('not_existing_user', False)

    def test_command_reset_user_token(self):
        AuthTokenCommand().create_user_token(self.user.username, False)
        first_token_key = Token.objects.first().key
        AuthTokenCommand().create_user_token(self.user.username, True)
        second_token_key = Token.objects.first().key

        assert first_token_key != second_token_key

    def test_command_do_not_reset_user_token(self):
        AuthTokenCommand().create_user_token(self.user.username, False)
        first_token_key = Token.objects.first().key
        AuthTokenCommand().create_user_token(self.user.username, False)
        second_token_key = Token.objects.first().key

        assert first_token_key == second_token_key

    def test_command_raising_error_for_invalid_user(self):
        out = StringIO()
        with pytest.raises(CommandError):
            call_command('drf_create_token', 'not_existing_user', stdout=out)

    def test_command_output(self):
        out = StringIO()
        call_command('drf_create_token', self.user.username, stdout=out)
        token_saved = Token.objects.first()
        self.assertIn('Generated token', out.getvalue())
        self.assertIn(self.user.username, out.getvalue())
        self.assertIn(token_saved.key, out.getvalue())
