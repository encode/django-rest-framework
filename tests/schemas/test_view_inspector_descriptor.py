import pytest
from django.test import TestCase, override_settings

from rest_framework.schemas.inspectors import AutoSchema, ViewInspector
from rest_framework.views import APIView


class CustomViewInspector(ViewInspector):
    """A dummy ViewInspector subclass"""
    pass


class TestViewInspector(TestCase):
    """
    Tests for the descriptor behaviour of ViewInspector
    (and subclasses.)
    """
    def test_apiview_schema_descriptor(self):
        view = APIView()
        assert hasattr(view, 'schema')
        assert isinstance(view.schema, AutoSchema)

    def test_set_custom_inspector_class_on_view(self):
        class CustomView(APIView):
            schema = CustomViewInspector()

        view = CustomView()
        assert isinstance(view.schema, CustomViewInspector)

    def test_set_custom_inspector_class_via_settings(self):
        with override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'tests.schemas.test_view_inspector_descriptor.CustomViewInspector'}):
            view = APIView()
            assert isinstance(view.schema, CustomViewInspector)

    def test_get_link_requires_instance(self):
        descriptor = APIView.schema  # Accessed from class
        with pytest.raises(AssertionError):
            descriptor.get_link(None, None, None)
