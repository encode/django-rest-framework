import importlib
from io import StringIO
from unittest.mock import patch

import pytest
from django.apps import apps
from django.contrib.admin import site
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.db import IntegrityError, connection, models
from django.db.models.signals import post_delete
from django.db.utils import ConnectionDoesNotExist
from django.test import TestCase, modify_settings, override_settings

from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.management.commands.drf_create_token import (
    Command as AuthTokenCommand
)
from rest_framework.authtoken.models import Token, TokenProxy
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError


def make_token_holder_model():
    """
    Build a model with a cascading FK to Token: any such relation pushes
    the deletion collector off the fast path, onto the one that deletes
    by `pk`.
    """
    class TokenHolder(models.Model):
        token = models.ForeignKey(Token, on_delete=models.CASCADE)

        class Meta:
            app_label = 'authtoken'

    return TokenHolder


class AuthTokenTests(TestCase):

    def setUp(self):
        self.site = site
        self.user = User.objects.create_user(username='test_user')
        self.token = Token.objects.create(key='test token', user=self.user)

    def test_authtoken_can_be_imported_when_not_included_in_installed_apps(self):
        import rest_framework.authtoken.models as authtoken_models
        originals = (authtoken_models.Token, authtoken_models.TokenProxy)
        try:
            with modify_settings(INSTALLED_APPS={'remove': 'rest_framework.authtoken'}):
                importlib.reload(authtoken_models)
        finally:
            # Set the proxy and abstract properties back to the version,
            # where authtoken is among INSTALLED_APPS.
            importlib.reload(authtoken_models)
            # Reloading registered new classes; put the originals back so
            # references held elsewhere stay valid.
            for model in originals:
                setattr(authtoken_models, model.__name__, model)
                apps.all_models['authtoken'][model._meta.model_name] = model
            apps.clear_cache()

    def test_model_admin_displayed_fields(self):
        mock_request = object()
        token_admin = TokenAdmin(self.token, self.site)
        assert token_admin.get_fields(mock_request) == ('user',)

    @patch('django.contrib.admin.site.register')  # avoid duplicate registrations
    def test_model_admin__username_field(self, mock_register):
        import rest_framework.authtoken.admin as authtoken_admin_m

        class EmailUser(User):
            USERNAME_FIELD = 'email'
            username = None

        for user_model in (User, EmailUser):
            with (
                self.subTest(user_model=user_model),
                patch('django.contrib.auth.get_user_model', return_value=user_model) as get_user_model
            ):
                importlib.reload(authtoken_admin_m)  # reload after patching
                assert get_user_model.call_count == 1

                mock_request = object()
                token_admin = authtoken_admin_m.TokenAdmin(TokenProxy, self.site)
                assert token_admin.get_search_fields(mock_request) == (f'user__{user_model.USERNAME_FIELD}',)
                assert token_admin.get_ordering(mock_request) == (f'user__{user_model.USERNAME_FIELD}',)

        importlib.reload(authtoken_admin_m)  # restore after testing

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
        user2 = User.objects.create_user('user2', 'user2@example.com', 'p')
        existing_token = Token.objects.create(user=user2)

        # Try to create another token with the same key
        with self.assertRaises(IntegrityError):
            Token.objects.create(key=existing_token.key, user=self.user)

    def test_key_generated_on_save_when_cleared(self):
        # Create a new user for this test to avoid conflicts with setUp token
        user2 = User.objects.create_user('test_user2', 'test2@example.com', 'password')

        # Create a token without a key - it should generate one automatically
        token = Token(user=user2)
        token.key = ""  # Explicitly clear the key
        token.save()

        # Verify the key was generated
        self.assertEqual(len(token.key), 40)
        self.assertEqual(token.user, user2)

    def test_clearing_key_on_existing_token_raises_integrity_error(self):
        """Test that clearing the key on an existing token raises IntegrityError."""
        user = User.objects.create_user('test_user3', 'test3@example.com', 'password')
        token = Token.objects.create(user=user)
        token.key = ""

        # This should raise IntegrityError because:
        # 1. We're trying to update a record with an empty primary key
        # 2. The OneToOneField constraint would be violated
        with self.assertRaises(Exception):  # Could be IntegrityError or DatabaseError
            token.save()

    def test_saving_existing_token_without_changes_does_not_alter_key(self):
        original_key = self.token.key

        self.token.save()
        self.assertEqual(self.token.key, original_key)

    def test_token_proxy_delete_deletes_the_token(self):
        deleted = TokenProxy.objects.get(user=self.user).delete()

        assert deleted == (1, {'authtoken.Token': 1})
        assert not Token.objects.filter(key='test token').exists()

    def test_token_proxy_delete_deletes_the_token_with_a_receiver_connected(self):
        fired = []

        def receiver(**kwargs):
            fired.append(kwargs['sender'])

        # The row is deleted as the concrete `Token`, so a receiver
        # connected to the proxy does not fire.
        post_delete.connect(receiver, sender=TokenProxy)
        self.addCleanup(post_delete.disconnect, receiver, sender=TokenProxy)

        TokenProxy.objects.get(user=self.user).delete()

        assert not Token.objects.exists()
        assert fired == []

    def test_token_proxy_delete_sends_signals_for_the_concrete_token(self):
        deleted = []

        def receiver(instance, **kwargs):
            # Copy the values out: the delete clears `instance.key` afterwards.
            deleted.append((instance.key, instance.user_id, instance.created))

        post_delete.connect(receiver, sender=Token)
        self.addCleanup(post_delete.disconnect, receiver, sender=Token)

        TokenProxy.objects.get(user=self.user).delete()

        assert deleted == [('test token', self.user.pk, self.token.created)]

    def test_token_proxy_queryset_delete_deletes_the_token(self):
        deleted = TokenProxy.objects.all().delete()

        assert deleted == (1, {'authtoken.Token': 1})
        assert not Token.objects.exists()

    def test_token_proxy_queryset_delete_leaves_other_tokens_alone(self):
        other_user = User.objects.create_user(username='other_user')
        other_token = Token.objects.create(key='other token', user=other_user)

        TokenProxy.objects.filter(user=self.user).delete()

        assert list(Token.objects.all()) == [other_token]

    def test_token_proxy_queryset_delete_follows_a_filter_across_a_join(self):
        other_user = User.objects.create_user(username='other_user')
        other_token = Token.objects.create(key='other token', user=other_user)

        TokenProxy.objects.filter(user__username='test_user').delete()

        assert list(Token.objects.all()) == [other_token]

    def test_token_proxy_delete_leaves_other_tokens_alone(self):
        other_user = User.objects.create_user(username='other_user')
        other_token = Token.objects.create(key='other token', user=other_user)

        TokenProxy.objects.get(user=self.user).delete()

        assert list(Token.objects.all()) == [other_token]

    def test_token_proxy_delete_deletes_a_deferred_token(self):
        proxy = TokenProxy.objects.defer('created').get(user=self.user)

        deleted, _ = proxy.delete()

        assert deleted == 1
        assert not Token.objects.exists()

    def test_token_proxy_delete_clears_the_key_and_refuses_a_second_delete(self):
        proxy = TokenProxy.objects.get(user=self.user)
        proxy.delete()

        assert proxy.key is None
        with pytest.raises(ValueError):
            proxy.delete()

    def test_model_admin_delete_model_deletes_the_token(self):
        token_admin = TokenAdmin(TokenProxy, self.site)
        proxy = TokenProxy.objects.get(user=self.user)

        token_admin.delete_model(object(), proxy)

        assert not Token.objects.exists()


class TokenProxyCascadeTests(TestCase):

    @classmethod
    def setUpClass(cls):
        # SQLite cannot run the schema editor inside the per-test transaction.
        cls.token_holder_model = make_token_holder_model()
        with connection.schema_editor() as editor:
            editor.create_model(cls.token_holder_model)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(cls.token_holder_model)
        del apps.all_models['authtoken']['tokenholder']
        apps.clear_cache()

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.token = Token.objects.create(key='test token', user=self.user)
        self.token_holder_model.objects.create(token=self.token)

    def test_token_proxy_delete_deletes_the_token_and_its_dependents(self):
        deleted, per_model = TokenProxy.objects.get(user=self.user).delete()

        assert deleted == 2
        assert per_model == {'authtoken.Token': 1, 'authtoken.TokenHolder': 1}
        assert not Token.objects.exists()
        assert not self.token_holder_model.objects.exists()

    def test_token_proxy_queryset_delete_deletes_the_token_and_its_dependents(self):
        # The dependent row stops the fast delete; the token used to survive.
        deleted, per_model = TokenProxy.objects.all().delete()

        assert deleted == 2
        assert per_model == {'authtoken.Token': 1, 'authtoken.TokenHolder': 1}
        assert not Token.objects.exists()
        assert not self.token_holder_model.objects.exists()


class UnreachableWriteRouter:
    def db_for_write(self, model, **hints):
        return 'nonexistent'


class TokenProxyRoutingTests(TestCase):
    databases = {'default', 'secondary'}

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.token = Token.objects.create(key='test token', user=self.user)
        secondary_user = User.objects.db_manager('secondary').create_user(
            username='secondary_user'
        )
        self.secondary_token = Token.objects.using('secondary').create(
            key='secondary token', user=secondary_user
        )

    def test_delete_uses_the_database_the_token_was_read_from(self):
        proxy = TokenProxy.objects.using('secondary').get(key='secondary token')

        proxy.delete()

        assert not Token.objects.using('secondary').exists()
        assert Token.objects.filter(key='test token').exists()

    def test_queryset_delete_uses_the_database_it_was_read_from(self):
        deleted, _ = TokenProxy.objects.using('secondary').delete()

        assert deleted == 1
        assert not Token.objects.using('secondary').exists()
        assert Token.objects.filter(key='test token').exists()

    @override_settings(DATABASE_ROUTERS=[UnreachableWriteRouter()])
    def test_delete_asks_the_router_which_database_writes_go_to(self):
        # The router decides writes, as it does for `Model.delete()`; reads
        # are unrouted, so the token is still found on `default`.
        proxy = TokenProxy.objects.get(key='test token')

        with pytest.raises(ConnectionDoesNotExist):
            proxy.delete()

        assert Token.objects.filter(key='test token').exists()

    @override_settings(DATABASE_ROUTERS=[UnreachableWriteRouter()])
    def test_queryset_delete_asks_the_router_which_database_writes_go_to(self):
        with pytest.raises(ConnectionDoesNotExist):
            TokenProxy.objects.filter(key='test token').delete()

        assert Token.objects.filter(key='test token').exists()


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
