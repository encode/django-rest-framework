from __future__ import unicode_literals

from django.test import TestCase
from django.utils import translation
from django.utils.translation import ugettext as _


class LocalizationTestCase(TestCase):

    def test_danish(self):
        translation.activate('da')
        self.assertEquals(_("Invalid token."), "Ugyldigt token.")
