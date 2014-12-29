from __future__ import unicode_literals
import warnings
from django.test import TestCase
from rest_framework.exceptions import \
    RESTFrameworkSettingHasUnexpectedClassWarning
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

    def test_bad_setting_class_raises_warning(self):
        """
        Make sure warnings are emitted when settings have an unexpected class.
        """
        settings = APISettings({
            'DEFAULT_RENDERER_CLASSES': 'rest_framework.renderers.JSONRenderer'
        })

        with warnings.catch_warnings(record=True) as w:
            # Trigger a warning.
            settings.DEFAULT_RENDERER_CLASSES
            # Verify that a warning is thrown
            assert len(w) == 1
            assert issubclass(
                w[-1].category, RESTFrameworkSettingHasUnexpectedClassWarning
            )
