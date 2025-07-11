from copy import deepcopy

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.test import TestCase, override_settings

from unittest import mock
from guardian.management import create_anonymous_user
from guardian.utils import get_anonymous_user


mocked_get_init_anon = mock.Mock()
multi_db_dict = {
    'default': deepcopy(settings.DATABASES['default']),
    'session': deepcopy(settings.DATABASES['default']),
}


class SessionRouter:
    @staticmethod
    def db_for_write(model, **kwargs):
        if model == Session:
            return 'session'
        else:
            return None

    @staticmethod
    def allow_migrate(db, app_label, **kwargs):
        if db == 'session':
            return app_label == 'sessions'
        else:
            return None


class TestGetAnonymousUser(TestCase):

    @mock.patch('guardian.management.guardian_settings')
    def test_uses_custom_function(self, guardian_settings):
        mocked_get_init_anon.reset_mock()

        path = 'guardian.testapp.tests.test_management.mocked_get_init_anon'
        guardian_settings.GET_INIT_ANONYMOUS_USER = path
        guardian_settings.ANONYMOUS_USER_NAME = "anonymous"
        User = get_user_model()

        anon = mocked_get_init_anon.return_value = mock.Mock()

        create_anonymous_user('sender', using='default')

        mocked_get_init_anon.assert_called_once_with(User)

        anon.save.assert_called_once_with(using='default')

    @mock.patch('guardian.management.guardian_settings')
    @override_settings(AUTH_USER_MODEL='testapp.CustomUsernameUser')
    def test_uses_custom_username_field_model(self, guardian_settings):
        mocked_get_init_anon.reset_mock()
        guardian_settings.GET_INIT_ANONYMOUS_USER = 'guardian.testapp.tests.test_management.mocked_get_init_anon'
        guardian_settings.ANONYMOUS_USER_NAME = 'testuser@example.com'
        User = get_user_model()

        anon = mocked_get_init_anon.return_value = mock.Mock()
        create_anonymous_user('sender', using='default')
        mocked_get_init_anon.assert_called_once_with(User)
        anon.save.assert_called_once_with(using='default')

    def test_get_anonymous_user(self):
        anon = get_anonymous_user()
        self.assertFalse(anon.has_usable_password())
        self.assertEqual(anon.get_username(), "AnonymousUser")

    @mock.patch('guardian.management.guardian_settings')
    @override_settings(
        DATABASE_ROUTERS=[SessionRouter()],
        DATABASES=multi_db_dict
    )
    def test_non_migrated_db(self, guardian_settings):
        mocked_get_init_anon.reset_mock()
        guardian_settings.GET_INIT_ANONYMOUS_USER = 'guardian.testapp.tests.test_management.mocked_get_init_anon'

        create_anonymous_user('sender', using='session')

        mocked_get_init_anon.assert_not_called()
