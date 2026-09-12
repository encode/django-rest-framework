import io
import os
import tempfile

import pytest
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import path

from rest_framework.compat import uritemplate, yaml
from rest_framework.utils import json
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

    @pytest.mark.skipif(yaml is None, reason='PyYAML is required.')
    def test_renders_default_schema_with_custom_title_url_and_description(self):
        call_command('generateschema',
                     '--title=ExampleAPI',
                     '--url=http://api.example.com',
                     '--description=Example description',
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
                     f'--generator_class={__name__}.{CustomSchemaGenerator.__name__}',
                     stdout=self.out)
        out_json = yaml.safe_load(self.out.getvalue())
        assert out_json == CustomSchemaGenerator.SCHEMA

    def test_writes_schema_to_file_on_parameter(self):
        fd, path = tempfile.mkstemp()
        try:
            call_command('generateschema', f'--file={path}', stdout=self.out)
            # nothing on stdout
            assert not self.out.getvalue()

            call_command('generateschema', stdout=self.out)
            expected_out = self.out.getvalue()
            # file output identical to stdout output
            with os.fdopen(fd) as fh:
                assert expected_out and fh.read() == expected_out
        finally:
            os.remove(path)
