from __future__ import unicode_literals

from django.test import TestCase

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

    def test_warning_raised_on_removed_setting(self):
        """
        Make sure user is alerted with an error when a removed setting
        is set.
        """
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            APISettings({
                'MAX_PAGINATE_BY': 100
            })
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[-1].category, DeprecationWarning))


class TestSettingTypes(TestCase):
    def test_settings_consistently_coerced_to_list(self):
        settings = APISettings({
            'DEFAULT_THROTTLE_CLASSES': ('rest_framework.throttling.BaseThrottle',)
        })
        self.assertTrue(isinstance(settings.DEFAULT_THROTTLE_CLASSES, list))

        settings = APISettings({
            'DEFAULT_THROTTLE_CLASSES': ()
        })
        self.assertTrue(isinstance(settings.DEFAULT_THROTTLE_CLASSES, list))
