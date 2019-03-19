from __future__ import unicode_literals

import pytest
from django.conf.urls import url
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import six

from rest_framework.compat import coreapi, yaml
from rest_framework.utils import json
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
    @pytest.mark.skipif(yaml is None, reason='PyYAML is required.')
    def test_renders_default_schema_with_custom_title_url_and_description(self):
        call_command('generateschema',
                     '--title=SampleAPI',
                     '--url=http://api.sample.com',
                     '--description=Sample description',
                     stdout=self.out)
        # Check valid YAML was output.
        schema = yaml.load(self.out.getvalue())
        assert schema['openapi'] == '3.0.2'

    def test_renders_openapi_json_schema(self):
        call_command('generateschema',
                     '--format=openapi-json',
                     stdout=self.out)
        # Check valid JSON was output.
        out_json = json.loads(self.out.getvalue())
        assert out_json['openapi'] == '3.0.2'
