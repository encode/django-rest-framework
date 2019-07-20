import pytest
from django.conf.urls import url
from django.test import RequestFactory, TestCase, override_settings

from rest_framework import filters, generics, pagination, routers, serializers
from rest_framework.compat import uritemplate
from rest_framework.request import Request
from rest_framework.schemas.openapi import AutoSchema, SchemaGenerator

from . import views


def create_request(path):
    factory = RequestFactory()
    request = Request(factory.get(path))
    return request


def create_view(view_cls, method, request):
    generator = SchemaGenerator()
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


class TestFieldMapping(TestCase):
    def test_list_field_mapping(self):
        inspector = AutoSchema()
        cases = [
            (serializers.ListField(), {'items': {}, 'type': 'array'}),
            (serializers.ListField(child=serializers.BooleanField()), {'items': {'type': 'boolean'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.FloatField()), {'items': {'type': 'number'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.CharField()), {'items': {'type': 'string'}, 'type': 'array'}),
        ]
        for field, mapping in cases:
            with self.subTest(field=field):
                assert inspector._map_field(field) == mapping


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
        inspector = AutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'ListExamples',
            'parameters': [],
            'responses': {'200': {'content': {'application/json': {'schema': {}}}}},
        }

    def test_path_with_id_parameter(self):
        path = '/example/{id}/'
        method = 'GET'

        view = create_view(
            views.ExampleDetailView,
            method,
            create_request(path)
        )
        inspector = AutoSchema()
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
        inspector = AutoSchema()
        inspector.view = view

        request_body = inspector._get_request_body(path, method)
        assert request_body['content']['application/json']['schema']['required'] == ['text']
        assert list(request_body['content']['application/json']['schema']['properties'].keys()) == ['text']

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
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        assert responses['200']['content']['application/json']['schema']['required'] == ['text']
        assert list(responses['200']['content']['application/json']['schema']['properties'].keys()) == ['text']

    def test_response_body_nested_serializer(self):
        path = '/'
        method = 'POST'

        class NestedSerializer(serializers.Serializer):
            number = serializers.IntegerField()

        class Serializer(serializers.Serializer):
            text = serializers.CharField()
            nested = NestedSerializer()

        class View(generics.GenericAPIView):
            serializer_class = Serializer

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        schema = responses['200']['content']['application/json']['schema']
        assert sorted(schema['required']) == ['nested', 'text']
        assert sorted(list(schema['properties'].keys())) == ['nested', 'text']
        assert schema['properties']['nested']['type'] == 'object'
        assert list(schema['properties']['nested']['properties'].keys()) == ['number']
        assert schema['properties']['nested']['required'] == ['number']

    def test_operation_id_generation(self):
        path = '/'
        method = 'GET'

        view = create_view(
            views.ExampleGenericAPIView,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        operationId = inspector._get_operation_id(path, method)
        assert operationId == 'ListExamples'

    def test_repeat_operation_ids(self):
        router = routers.SimpleRouter()
        router.register('account', views.ExampleGenericViewSet, basename="account")
        urlpatterns = router.urls

        generator = SchemaGenerator(patterns=urlpatterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)
        schema_str = str(schema)
        print(schema_str)
        assert schema_str.count("operationId") == 2
        assert schema_str.count("newExample") == 1
        assert schema_str.count("oldExample") == 1


@pytest.mark.skipif(uritemplate is None, reason='uritemplate not installed.')
@override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema'})
class TestGenerator(TestCase):

    def test_override_settings(self):
        assert isinstance(views.ExampleListView.schema, AutoSchema)

    def test_paths_construction(self):
        """Construction of the `paths` key."""
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)
        generator._initialise_endpoints()

        paths = generator.get_paths()

        assert '/example/' in paths
        example_operations = paths['/example/']
        assert len(example_operations) == 2
        assert 'get' in example_operations
        assert 'post' in example_operations

    def test_prefixed_paths_construction(self):
        """Construction of the `paths` key maintains a common prefix."""
        patterns = [
            url(r'^v1/example/?$', views.ExampleListView.as_view()),
            url(r'^v1/example/{pk}/?$', views.ExampleDetailView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)
        generator._initialise_endpoints()

        paths = generator.get_paths()

        assert '/v1/example/' in paths
        assert '/v1/example/{id}/' in paths

    def test_mount_url_prefixed_to_paths(self):
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
            url(r'^example/{pk}/?$', views.ExampleDetailView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns, url='/api')
        generator._initialise_endpoints()

        paths = generator.get_paths()

        assert '/api/example/' in paths
        assert '/api/example/{id}/' in paths

    def test_schema_construction(self):
        """Construction of the top level dictionary."""
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        assert 'openapi' in schema
        assert 'paths' in schema

    def test_serializer_datefield(self):
        patterns = [
            url(r'^example/?$', views.ExampleGenericViewSet.as_view({"get": "get"})),
        ]
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        response = schema['paths']['/example/']['get']['responses']
        response_schema = response['200']['content']['application/json']['schema']['properties']

        assert response_schema['date']['type'] == response_schema['datetime']['type'] == 'string'

        assert response_schema['date']['format'] == 'date'
        assert response_schema['datetime']['format'] == 'date-time'

    def test_serializer_validators(self):
        patterns = [
            url(r'^example/?$', views.ExampleValdidatedAPIView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        response = schema['paths']['/example/']['get']['responses']
        response_schema = response['200']['content']['application/json']['schema']['properties']

        assert response_schema['integer']['type'] == 'integer'
        assert response_schema['integer']['maximum'] == 99
        assert response_schema['integer']['minimum'] == -11

        assert response_schema['string']['minLength'] == 2
        assert response_schema['string']['maxLength'] == 10

        assert response_schema['regex']['pattern'] == r'[ABC]12{3}'
        assert response_schema['regex']['description'] == 'must have an A, B, or C followed by 1222'

        assert response_schema['decimal1']['type'] == 'number'
        assert response_schema['decimal1']['multipleOf'] == .01
        assert response_schema['decimal1']['maximum'] == 10000
        assert response_schema['decimal1']['minimum'] == -10000

        assert response_schema['decimal2']['type'] == 'number'
        assert response_schema['decimal2']['multipleOf'] == .0001

        assert response_schema['email']['type'] == 'string'
        assert response_schema['email']['format'] == 'email'
        assert response_schema['email']['default'] == 'foo@bar.com'

        assert response_schema['url']['type'] == 'string'
        assert response_schema['url']['nullable'] is True
        assert response_schema['url']['default'] == 'http://www.example.com'

        assert response_schema['uuid']['type'] == 'string'
        assert response_schema['uuid']['format'] == 'uuid'

        assert response_schema['ip4']['type'] == 'string'
        assert response_schema['ip4']['format'] == 'ipv4'

        assert response_schema['ip6']['type'] == 'string'
        assert response_schema['ip6']['format'] == 'ipv6'

        assert response_schema['ip']['type'] == 'string'
        assert 'format' not in response_schema['ip']
