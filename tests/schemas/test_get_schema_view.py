from django.test import TestCase

from rest_framework import renderers
from rest_framework.schemas import get_schema_view, openapi


class GetSchemaViewTests(TestCase):
    """For the get_schema_view() helper."""
    def test_openapi(self):
        schema_view = get_schema_view(title="With OpenAPI")
        assert isinstance(schema_view.initkwargs['schema_generator'], openapi.SchemaGenerator)
        assert renderers.OpenAPIRenderer in schema_view.cls().renderer_classes
