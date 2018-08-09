from django.conf.urls import url
from django.test import RequestFactory, TestCase, override_settings

from rest_framework.request import Request
from rest_framework.schemas.generators import OpenAPISchemaGenerator
from rest_framework.schemas.inspectors import OpenAPIAutoSchema

from . import views


def create_request(path):
    factory = RequestFactory()
    request = Request(factory.get(path))
    return request


def create_view(view_cls, method, request):
    generator = OpenAPISchemaGenerator()
    view = generator.create_view(view_cls.as_view(), method, request)
    return view


class TestInspector(TestCase):

    def test_path_without_parameters(self):
        path = '/example/'
        method = 'GET'

        view = create_view(
            views.ExampleListView,
            method,
            create_request(path)
        )
        inspector = OpenAPIAutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {}

    # TODO: parameters, operationID, responses, etc ???


@override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.inspectors.OpenAPIAutoSchema'})
class TestGenerator(TestCase):

    def test_paths_construction(self):
        """Construction of the `paths` key."""
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
        ]
        generator = OpenAPISchemaGenerator(patterns=patterns)
        generator._initialise_endpoints()

        paths = generator.get_paths()

        assert 'example/' in paths
        example_operations = paths['example/']
        assert len(example_operations) == 2
        assert 'get' in example_operations
        assert 'post' in example_operations

    def test_schema_construction(self):
        """Construction of the top level dictionary."""
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
        ]
        generator = OpenAPISchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        assert 'basePath' in schema
        assert 'paths' in schema
