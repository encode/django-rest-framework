# encoding: utf-8
from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.templatetags.rest_framework import add_query_param, urlize_quoted_links

factory = APIRequestFactory()


class TemplateTagTests(TestCase):

    def test_add_query_param_with_non_latin_charactor(self):
        # Ensure we don't double-escape non-latin characters
        # that are present in the querystring.
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
        _ = urlize_quoted_links("asdf:[/p]zxcv.com")
