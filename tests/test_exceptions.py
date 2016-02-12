from __future__ import unicode_literals

from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from rest_framework.exceptions import _force_text_recursive


class ExceptionTestCase(TestCase):

    def test_force_text_recursive(self):

        s = "sfdsfggiuytraetfdlklj"
        self.assertEqual(_force_text_recursive(_(s)), s)
        self.assertEqual(type(_force_text_recursive(_(s))), type(s))

        self.assertEqual(_force_text_recursive({'a': _(s)})['a'], s)
        self.assertEqual(type(_force_text_recursive({'a': _(s)})['a']), type(s))

        self.assertEqual(_force_text_recursive([[_(s)]])[0][0], s)
        self.assertEqual(type(_force_text_recursive([[_(s)]])[0][0]), type(s))
