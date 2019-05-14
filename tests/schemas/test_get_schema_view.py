import pytest
from django.test import TestCase, override_settings

from rest_framework import renderers
from rest_framework.schemas import coreapi, get_schema_view, openapi


class GetSchemaViewTests(TestCase):
    """For the get_schema_view() helper."""
    def test_openapi(self):
        schema_view = get_schema_view(title="With OpenAPI")
        assert isinstance(schema_view.initkwargs['schema_generator'], openapi.SchemaGenerator)
        assert renderers.OpenAPIRenderer in schema_view.cls().renderer_classes

    @pytest.mark.skipif(not coreapi.coreapi, reason='coreapi is not installed')
    def test_coreapi(self):
        with override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.AutoSchema'}):
            schema_view = get_schema_view(title="With CoreAPI")
            assert isinstance(schema_view.initkwargs['schema_generator'], coreapi.SchemaGenerator)
            assert renderers.CoreAPIOpenAPIRenderer in schema_view.cls().renderer_classes
