from __future__ import unicode_literals
from django.core.exceptions import ImproperlyConfigured
import pytest
from django.test import TestCase
from django.utils import six
from rest_framework.settings import APISettings


class TestSettings(TestCase):
    def test_import_error_message_maintained(self):
        """
        Make sure import errors are captured and raised sensibly.
        """
        settings = APISettings({
            'DEFAULT_RENDERER_CLASSES': [
                'tests.invalid_module.InvalidClassName'
            ]
        })
        with self.assertRaises(ImportError):
            settings.DEFAULT_RENDERER_CLASSES

    def test_bad_iterable_setting_class_raises_warning(self):
        """
        Make sure errors are raised when settings which should be iterable are
        not.
        """
        settings = APISettings({
            'DEFAULT_RENDERER_CLASSES': 'rest_framework.renderers.JSONRenderer'
        })

        # Trigger the exception
        with pytest.raises(ImproperlyConfigured) as exc_info:
            settings.DEFAULT_RENDERER_CLASSES

        # Construct the expected error message
        text_type_name = str(six.text_type.__name__)
        expected_error = (
            u'The "DEFAULT_RENDERER_CLASSES" setting must be a list or '
            u'tuple, but got type "{text_type_name}" with value '
            u'"rest_framework.renderers.JSONRenderer".'.format(
                text_type_name=text_type_name
            )
        )
        assert exc_info.value.args[0] == expected_error

    def test_bad_string_setting_class_raises_warning(self):
        """
        Make sure errors are raised when settings which should be strings are
        not.
        """
        settings = APISettings({
            'DEFAULT_METADATA_CLASS': []
        })

        # Trigger the exception
        with pytest.raises(ImproperlyConfigured) as exc_info:
            settings.DEFAULT_METADATA_CLASS

        expected_error = (
            u'The "DEFAULT_METADATA_CLASS" setting must be a string, but got '
            u'type "list" with value "[]".'
        )
        assert exc_info.value.args[0] == expected_error
