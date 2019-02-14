from __future__ import unicode_literals

import pytest
from django.conf.urls import url
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import six

from rest_framework.compat import coreapi
from rest_framework.utils import formatting, json
from rest_framework.views import APIView


class FooView(APIView):
    def get(self, request):
        pass


urlpatterns = [
    url(r'^$', FooView.as_view())
]


@override_settings(ROOT_URLCONF='tests.test_generateschema')
@pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
class GenerateSchemaTests(TestCase):
    """Tests for management command generateschema."""

    def setUp(self):
        self.out = six.StringIO()

    @pytest.mark.skipif(six.PY2, reason='PyYAML unicode output is malformed on PY2.')
    def test_renders_default_schema_with_custom_title_url_and_description(self):
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

        self.assertIn(formatting.dedent(expected_out), self.out.getvalue())

    def test_renders_openapi_json_schema(self):
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

    def test_renders_corejson_schema(self):
        expected_out = """{"_type":"document","":{"list":{"_type":"link","url":"/","action":"get"}}}"""
        call_command('generateschema',
                     '--format=corejson',
                     stdout=self.out)
        self.assertIn(expected_out, self.out.getvalue())
