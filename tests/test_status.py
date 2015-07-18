from __future__ import unicode_literals

from django.test import TestCase

from rest_framework.status import (
    is_client_error, is_informational, is_redirect, is_server_error,
    is_success
)


class TestStatus(TestCase):
    def test_status_categories(self):
        self.assertFalse(is_informational(99))
        self.assertTrue(is_informational(100))
        self.assertTrue(is_informational(199))
        self.assertFalse(is_informational(200))

        self.assertFalse(is_success(199))
        self.assertTrue(is_success(200))
        self.assertTrue(is_success(299))
        self.assertFalse(is_success(300))

        self.assertFalse(is_redirect(299))
        self.assertTrue(is_redirect(300))
        self.assertTrue(is_redirect(399))
        self.assertFalse(is_redirect(400))

        self.assertFalse(is_client_error(399))
        self.assertTrue(is_client_error(400))
        self.assertTrue(is_client_error(499))
        self.assertFalse(is_client_error(500))

        self.assertFalse(is_server_error(499))
        self.assertTrue(is_server_error(500))
        self.assertTrue(is_server_error(599))
        self.assertFalse(is_server_error(600))
