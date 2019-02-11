from __future__ import unicode_literals

import django
import pytest
from django.conf.urls import url
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from six import StringIO

from rest_framework.compat import coreapi
from rest_framework.utils import json
from rest_framework.views import APIView


class FooView(APIView):  # noqa
    def get(self, request):  # noqa
        pass


urlpatterns = [
    url(r'^$', FooView.as_view())
]


@override_settings(ROOT_URLCONF='tests.test_generateschema')
@pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
class GenerateSchemaTests(TestCase):
    """Tests for management command generateschema."""

    def setUp(self):  # noqa
        self.out = StringIO()

    @pytest.mark.skipif(django.VERSION < (2, 1), reason='Django version < 2.1')
    def test_should_render_default_schema_with_custom_title_url_and_description(self):  # noqa
        expected_out = """info:
  description: Sample description
  title: SampleAPI
  version: ''
openapi: 3.0.0
paths:
  /:
    get:
      operationId: list
servers:
- url: http://api.sample.com/
"""
        call_command('generateschema',
                     '--title=SampleAPI',
                     '--url=http://api.sample.com',
                     '--description=Sample description',
                     stdout=self.out)

        self.assertIn(expected_out, self.out.getvalue())

    def test_should_render_openapi_json_schema(self):  # noqa
        expected_out = {
            "openapi": "3.0.0",
            "info": {
                "version": "",
                "title": "",
                "description": ""
            },
            "servers": [
                {
                    "url": ""
                }
            ],
            "paths": {
                "/": {
                    "get": {
                        "operationId": "list"
                    }
                }
            }
        }
        call_command('generateschema',
                     '--format=openapi-json',
                     stdout=self.out)
        out_json = json.loads(self.out.getvalue())

        self.assertDictEqual(out_json, expected_out)

    def test_should_render_corejson_schema(self):  # noqa
        expected_out = """{"_type":"document","":{"list":{"_type":"link","url":"/","action":"get"}}}"""  # noqa
        call_command('generateschema',
                     '--format=corejson',
                     stdout=self.out)
        self.assertIn(expected_out, self.out.getvalue())
