from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from unittest import mock
from guardian.conf import settings as guardian_settings
from guardian.ctypes import get_content_type


class TestConfiguration(TestCase):

    def test_check_configuration(self):

        with mock.patch('guardian.conf.settings.RENDER_403', True):
            with mock.patch('guardian.conf.settings.RAISE_403', True):
                self.assertRaises(ImproperlyConfigured,
                                  guardian_settings.check_configuration)

    def test_get_content_type(self):
        with mock.patch('guardian.conf.settings.GET_CONTENT_TYPE', 'guardian.testapp.tests.test_conf.get_test_content_type'):
            self.assertEqual(get_content_type(None), 'x')


def get_test_content_type(obj):
    """ Used in TestConfiguration.test_get_content_type()."""
    return 'x'
