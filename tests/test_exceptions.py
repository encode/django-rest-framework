from __future__ import unicode_literals

from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import ErrorMessage, _force_text_recursive


class ExceptionTestCase(TestCase):

    def test_force_text_recursive(self):

        s = "sfdsfggiuytraetfdlklj"
        self.assertEqual(_force_text_recursive(_(s)), s)
        assert isinstance(_force_text_recursive(_(s)), ErrorMessage)

        self.assertEqual(_force_text_recursive({'a': _(s)})['a'], s)
        assert isinstance(_force_text_recursive({'a': _(s)})['a'], ErrorMessage)

        self.assertEqual(_force_text_recursive([[_(s)]])[0][0], s)
        assert isinstance(_force_text_recursive([[_(s)]])[0][0], ErrorMessage)
