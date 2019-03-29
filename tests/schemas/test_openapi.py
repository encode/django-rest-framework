import pytest
from django.conf.urls import url
from django.test import RequestFactory, TestCase, override_settings

from rest_framework import filters, generics, pagination, serializers
from rest_framework.compat import uritemplate
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


class TestBasics(TestCase):
    def dummy_view(request):
        pass

    def test_filters(self):
        classes = [filters.SearchFilter, filters.OrderingFilter]
        for c in classes:
            f = c()
            assert f.get_schema_operation_parameters(self.dummy_view)

    def test_pagination(self):
        classes = [pagination.PageNumberPagination, pagination.LimitOffsetPagination, pagination.CursorPagination]
        for c in classes:
            f = c()
            assert f.get_schema_operation_parameters(self.dummy_view)


@pytest.mark.skipif(uritemplate is None, reason='uritemplate not installed.')
class TestOperationIntrospection(TestCase):

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
        assert operation == {
            'operationId': 'ListExamples',
            'parameters': [],
            'responses': {'200': {'content': {'application/json': {}}}},
        }

    def test_path_with_id_parameter(self):
        path = '/example/{id}/'
        method = 'GET'

        view = create_view(
            views.ExampleDetailView,
            method,
            create_request(path)
        )
        inspector = OpenAPIAutoSchema()
        inspector.view = view

        parameters = inspector._get_path_parameters(path, method)
        assert parameters == [{
            'description': '',
            'in': 'path',
            'name': 'id',
            'required': True,
            'schema': {
                'type': 'string',
            },
        }]

    def test_request_body(self):
        path = '/'
        method = 'POST'

        class Serializer(serializers.Serializer):
            text = serializers.CharField()
            read_only = serializers.CharField(read_only=True)

        class View(generics.GenericAPIView):
            serializer_class = Serializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        inspector = OpenAPIAutoSchema()
        inspector.view = view

        request_body = inspector._get_request_body(path, method)
        assert request_body['content']['application/json']['required'] == ['text']
        assert list(request_body['content']['application/json']['properties'].keys()) == ['text']

    def test_response_body_generation(self):
        path = '/'
        method = 'POST'

        class Serializer(serializers.Serializer):
            text = serializers.CharField()
            write_only = serializers.CharField(write_only=True)

        class View(generics.GenericAPIView):
            serializer_class = Serializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        inspector = OpenAPIAutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        assert responses['200']['content']['application/json']['required'] == ['text']
        assert list(responses['200']['content']['application/json']['properties'].keys()) == ['text']


@pytest.mark.skipif(uritemplate is None, reason='uritemplate not installed.')
@override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.inspectors.OpenAPIAutoSchema'})
class TestGenerator(TestCase):

    def test_override_settings(self):
        assert isinstance(views.ExampleListView.schema, OpenAPIAutoSchema)

    def test_paths_construction(self):
        """Construction of the `paths` key."""
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
        ]
        generator = OpenAPISchemaGenerator(patterns=patterns)
        generator._initialise_endpoints()

        paths = generator.get_paths()

        assert '/example/' in paths
        example_operations = paths['/example/']
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

        assert 'openapi' in schema
        assert 'paths' in schema
