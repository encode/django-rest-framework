# encoding: utf-8
from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.templatetags.rest_framework import add_query_param, urlize_quoted_links


factory = APIRequestFactory()


class TemplateTagTests(TestCase):

    def test_add_query_param_with_non_latin_charactor(self):
        # Ensure we don't double-escape non-latin characters
        # that are present in the querystring.
        # See #1314.
        request = factory.get("/", {'q': '查询'})
        json_url = add_query_param(request, "format", "json")
        self.assertIn("q=%E6%9F%A5%E8%AF%A2", json_url)
        self.assertIn("format=json", json_url)


class Issue1386Tests(TestCase):
    """
    Covers #1386
    """

    def test_issue_1386(self):
        """
        Test function urlize_quoted_links with different args
        """
        correct_urls = [
            "asdf.com",
            "asdf.net",
            "www.as_df.org",
            "as.d8f.ghj8.gov",
        ]
        for i in correct_urls:
            res = urlize_quoted_links(i)
            self.assertNotEqual(res, i)
            self.assertIn(i, res)

        incorrect_urls = [
            "mailto://asdf@fdf.com",
            "asdf.netnet",
        ]
        for i in incorrect_urls:
            res = urlize_quoted_links(i)
            self.assertEqual(i, res)

        # example from issue #1386, this shouldn't raise an exception
        urlize_quoted_links("asdf:[/p]zxcv.com")


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
