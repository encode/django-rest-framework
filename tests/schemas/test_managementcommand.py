import io
import os
import tempfile

import pytest
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import path

from rest_framework.compat import uritemplate, yaml
from rest_framework.management.commands import generateschema
from rest_framework.utils import formatting, json
from rest_framework.views import APIView


class FooView(APIView):
    def get(self, request):
        pass


urlpatterns = [
    path('', FooView.as_view())
]


class CustomSchemaGenerator:
    SCHEMA = {"key": "value"}

    def __init__(self, *args, **kwargs):
        pass

    def get_schema(self, **kwargs):
        return self.SCHEMA


@override_settings(ROOT_URLCONF=__name__)
@pytest.mark.skipif(not uritemplate, reason='uritemplate is not installed')
class GenerateSchemaTests(TestCase):
    """Tests for management command generateschema."""

    def setUp(self):
        self.out = io.StringIO()

    def test_command_detects_schema_generation_mode(self):
        """Switching between CoreAPI & OpenAPI"""
        command = generateschema.Command()
        assert command.get_mode() == generateschema.OPENAPI_MODE
        with override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema'}):
            assert command.get_mode() == generateschema.COREAPI_MODE

    @pytest.mark.skipif(yaml is None, reason='PyYAML is required.')
    def test_renders_default_schema_with_custom_title_url_and_description(self):
        call_command('generateschema',
                     '--title=SampleAPI',
                     '--url=http://api.sample.com',
                     '--description=Sample description',
                     stdout=self.out)
        # Check valid YAML was output.
        schema = yaml.safe_load(self.out.getvalue())
        assert schema['openapi'] == '3.0.2'

    def test_renders_openapi_json_schema(self):
        call_command('generateschema',
                     '--format=openapi-json',
                     stdout=self.out)
        # Check valid JSON was output.
        out_json = json.loads(self.out.getvalue())
        assert out_json['openapi'] == '3.0.2'

    def test_accepts_custom_schema_generator(self):
        call_command('generateschema',
                     '--generator_class={}.{}'.format(__name__, CustomSchemaGenerator.__name__),
                     stdout=self.out)
        out_json = yaml.safe_load(self.out.getvalue())
        assert out_json == CustomSchemaGenerator.SCHEMA

    def test_writes_schema_to_file_on_parameter(self):
        fd, path = tempfile.mkstemp()
        try:
            call_command('generateschema', '--file={}'.format(path), stdout=self.out)
            # nothing on stdout
            assert not self.out.getvalue()

            call_command('generateschema', stdout=self.out)
            expected_out = self.out.getvalue()
            # file output identical to stdout output
            with os.fdopen(fd) as fh:
                assert expected_out and fh.read() == expected_out
        finally:
            os.remove(path)

    @pytest.mark.skipif(yaml is None, reason='PyYAML is required.')
    @override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema'})
    def test_coreapi_renders_default_schema_with_custom_title_url_and_description(self):
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

    @override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema'})
    def test_coreapi_renders_openapi_json_schema(self):
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

    @override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema'})
    def test_renders_corejson_schema(self):
        expected_out = """{"_type":"document","":{"list":{"_type":"link","url":"/","action":"get"}}}"""
        call_command('generateschema',
                     '--format=corejson',
                     stdout=self.out)
        self.assertIn(expected_out, self.out.getvalue())
