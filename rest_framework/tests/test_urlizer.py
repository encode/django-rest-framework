from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.templatetags.rest_framework import urlize_quoted_links
import sys


class URLizerTests(TestCase):
    """
    Test if both JSON and YAML URLs are transformed into links well
    """
    def _urlize_dict_check(self, data):
        """
        For all items in dict test assert that the value is urlized key
        """
        for original, urlized in data.items():
            assert urlize_quoted_links(original, nofollow=False) == urlized

    def test_json_with_url(self):
        """
        Test if JSON URLs are transformed into links well
        """
        data = {}
        data['"url": "http://api/users/1/", '] = \
            '&quot;url&quot;: &quot;<a href="http://api/users/1/">http://api/users/1/</a>&quot;, '
        data['"foo_set": [\n    "http://api/foos/1/"\n], '] = \
            '&quot;foo_set&quot;: [\n    &quot;<a href="http://api/foos/1/">http://api/foos/1/</a>&quot;\n], '
        self._urlize_dict_check(data)

    def test_yaml_with_url(self):
        """
        Test if YAML URLs are transformed into links well
        """
        data = {}
        data['''{users: 'http://api/users/'}'''] = \
            '''{users: &#39;<a href="http://api/users/">http://api/users/</a>&#39;}'''
        data['''foo_set: ['http://api/foos/1/']'''] = \
            '''foo_set: [&#39;<a href="http://api/foos/1/">http://api/foos/1/</a>&#39;]'''
        self._urlize_dict_check(data)
