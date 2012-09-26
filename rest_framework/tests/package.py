"""Tests for the rest_framework package setup."""
from django.test import TestCase
import rest_framework

class TestVersion(TestCase):
    """Simple sanity test to check the VERSION exists"""

    def test_version(self):
        """Ensure the VERSION exists."""
        rest_framework.VERSION

