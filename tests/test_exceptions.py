from __future__ import unicode_literals

from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ErrorDetail, _get_error_details


class ExceptionTestCase(TestCase):

    def test_get_error_details(self):

        example = "string"
        lazy_example = _(example)

        self.assertEqual(
            _get_error_details(lazy_example),
            example
        )
        assert isinstance(
            _get_error_details(lazy_example),
            ErrorDetail
        )

        self.assertEqual(
            _get_error_details({'nested': lazy_example})['nested'],
            example
        )
        assert isinstance(
            _get_error_details({'nested': lazy_example})['nested'],
            ErrorDetail
        )

        self.assertEqual(
            _get_error_details([[lazy_example]])[0][0],
            example
        )
        assert isinstance(
            _get_error_details([[lazy_example]])[0][0],
            ErrorDetail
        )
