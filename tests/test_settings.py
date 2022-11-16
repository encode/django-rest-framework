from django.test import TestCase, override_settings

from rest_framework.settings import APISettings, api_settings


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
        with self.assertRaises(RuntimeError):
            APISettings({
                'MAX_PAGINATE_BY': 100
            })

    def test_compatibility_with_override_settings(self):
        """
        Ref #5658 & #2466: Documented usage of api_settings
        is bound at import time:

            from rest_framework.settings import api_settings

        setting_changed signal hook must ensure bound instance
        is refreshed.
        """
        assert api_settings.PAGE_SIZE is None, "Checking a known default should be None"

        with override_settings(REST_FRAMEWORK={'PAGE_SIZE': 10}):
            assert api_settings.PAGE_SIZE == 10, "Setting should have been updated"

        assert api_settings.PAGE_SIZE is None, "Setting should have been restored"


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
