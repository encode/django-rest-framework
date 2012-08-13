"""Tests for the status module"""
from django.test import TestCase
from djangorestframework import status


class TestStatus(TestCase):
    """Simple sanity test to check the status module"""

    def test_status(self):
        """Ensure the status module is present and correct."""
        self.assertEquals(200, status.HTTP_200_OK)
        self.assertEquals(404, status.HTTP_404_NOT_FOUND)
