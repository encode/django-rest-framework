"""Tests for the settings module"""
from __future__ import unicode_literals
from django.test import TestCase

from rest_framework.settings import APISettings, DEFAULTS, IMPORT_STRINGS


class TestSettings(TestCase):
    """Tests relating to the api settings"""

    def test_non_import_errors(self):
        """Make sure other errors aren't suppressed."""
        settings = APISettings({'DEFAULT_MODEL_SERIALIZER_CLASS': 'rest_framework.tests.extras.bad_import.ModelSerializer'}, DEFAULTS, IMPORT_STRINGS)
        with self.assertRaises(ValueError):
            settings.DEFAULT_MODEL_SERIALIZER_CLASS

    def test_import_error_message_maintained(self):
        """Make sure real import errors are captured and raised sensibly."""
        settings = APISettings({'DEFAULT_MODEL_SERIALIZER_CLASS': 'rest_framework.tests.extras.not_here.ModelSerializer'}, DEFAULTS, IMPORT_STRINGS)
        with self.assertRaises(ImportError) as cm:
            settings.DEFAULT_MODEL_SERIALIZER_CLASS
        self.assertTrue('ImportError' in str(cm.exception))
