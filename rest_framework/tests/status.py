"""Tests for the status module"""
from __future__ import unicode_literals
from django.test import TestCase
from rest_framework import status


class TestStatus(TestCase):
    """Simple sanity test to check the status module"""

    def test_status(self):
        """Ensure the status module is present and correct."""
        self.assertEqual(200, status.HTTP_200_OK)
        self.assertEqual(404, status.HTTP_404_NOT_FOUND)
