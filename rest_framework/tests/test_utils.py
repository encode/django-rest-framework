# -*- coding: utf-8 -*-

from django.test import TestCase
from rest_framework.utils import formatting
import sys


class FormattingUnitTests(TestCase):
    def setUp(self):
        # test strings snatched from http://www.columbia.edu/~fdc/utf8/,
        # http://winrus.com/utf8-jap.htm and memory
        self.utf8_test_string = (
            'zażółć gęślą jaźń'
            'Sîne klâwen durh die wolken sint geslagen'
            'Τη γλώσσα μου έδωσαν ελληνική'
            'யாமறிந்த மொழிகளிலே தமிழ்மொழி'
            'На берегу пустынных волн'
            ' てすと'
            'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃ'
        )
        self.non_utf8_test_string = ('The quick brown fox jumps over the lazy '
                                     'dog')

    def test_for_ascii_support_in_remove_leading_indent(self):
        if sys.version_info < (3, 0):
            # only Python 2.x is affected, so we skip the test entirely
            # if on Python 3.x
            self.assertEqual(formatting._remove_leading_indent(
                self.non_utf8_test_string), self.non_utf8_test_string)

    def test_for_utf8_support_in_remove_leading_indent(self):
        if sys.version_info < (3, 0):
            # only Python 2.x is affected, so we skip the test entirely
            # if on Python 3.x
            self.assertEqual(formatting._remove_leading_indent(
                self.utf8_test_string), self.utf8_test_string.decode('utf-8'))
