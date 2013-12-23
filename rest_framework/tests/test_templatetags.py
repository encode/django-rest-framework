# encoding: utf-8
from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework.templatetags.rest_framework import add_query_param

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
