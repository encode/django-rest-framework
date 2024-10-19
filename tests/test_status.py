from django.test import TestCase

from rest_framework.status import (
    is_client_error, is_informational, is_redirect, is_server_error, is_success
)


class TestStatus(TestCase):
    def test_status_categories(self):
        assert not is_informational(99)
        assert is_informational(100)
        assert is_informational(199)
        assert not is_informational(200)

        assert not is_success(199)
        assert is_success(200)
        assert is_success(299)
        assert not is_success(300)

        assert not is_redirect(299)
        assert is_redirect(300)
        assert is_redirect(399)
        assert not is_redirect(400)

        assert not is_client_error(399)
        assert is_client_error(400)
        assert is_client_error(499)
        assert not is_client_error(500)

        assert not is_server_error(499)
        assert is_server_error(500)
        assert is_server_error(599)
        assert not is_server_error(600)
