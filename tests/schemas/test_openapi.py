import pytest
from django.conf.urls import url
from django.test import RequestFactory, TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from rest_framework import filters, generics, pagination, routers, serializers
from rest_framework.compat import uritemplate
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.renderers import JSONRenderer
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
            (serializers.ListField(child=serializers.IntegerField(max_value=4294967295)),
             {'items': {'type': 'integer', 'format': 'int64'}, 'type': 'array'}),
            (serializers.IntegerField(min_value=2147483648),
             {'type': 'integer', 'minimum': 2147483648, 'format': 'int64'}),
        ]
        for field, mapping in cases:
            with self.subTest(field=field):
                assert inspector._map_field(field) == mapping

    def test_lazy_string_field(self):
        class Serializer(serializers.Serializer):
            text = serializers.CharField(help_text=_('lazy string'))

        inspector = AutoSchema()

        data = inspector._map_serializer(Serializer())
        assert isinstance(data['properties']['text']['description'], str), "description must be str"


@pytest.mark.skipif(uritemplate is None, reason='uritemplate not installed.')
class TestOperationIntrospection(TestCase):

    def test_path_without_parameters(self):
        path = '/example/'
        method = 'GET'

        view = create_view(
            views.DocStringExampleListView,
            method,
            create_request(path)
        )
        inspector = AutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'listDocStringExamples',
            'description': 'A description of my GET operation.',
            'parameters': [],
            'responses': {
                '200': {
                    'description': '',
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'array',
                                'items': {},
                            },
                        },
                    },
                },
            },
        }

    def test_path_with_id_parameter(self):
        path = '/example/{id}/'
        method = 'GET'

        view = create_view(
            views.DocStringExampleDetailView,
            method,
            create_request(path)
        )
        inspector = AutoSchema()
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'RetrieveDocStringExampleDetail',
            'description': 'A description of my GET operation.',
            'parameters': [{
                'description': '',
                'in': 'path',
                'name': 'id',
                'required': True,
                'schema': {
                    'type': 'string',
                },
            }],
            'responses': {
                '200': {
                    'description': '',
                    'content': {
                        'application/json': {
                            'schema': {
                            },
                        },
                    },
                },
            },
        }

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

    def test_empty_required(self):
        path = '/'
        method = 'POST'

        class Serializer(serializers.Serializer):
            read_only = serializers.CharField(read_only=True)
            write_only = serializers.CharField(write_only=True, required=False)

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
        # there should be no empty 'required' property, see #6834
        assert 'required' not in request_body['content']['application/json']['schema']

        for response in inspector._get_responses(path, method).values():
            assert 'required' not in response['content']['application/json']['schema']

    def test_empty_required_with_patch_method(self):
        path = '/'
        method = 'PATCH'

        class Serializer(serializers.Serializer):
            read_only = serializers.CharField(read_only=True)
            write_only = serializers.CharField(write_only=True, required=False)

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
        # there should be no empty 'required' property, see #6834
        assert 'required' not in request_body['content']['application/json']['schema']
        for response in inspector._get_responses(path, method).values():
            assert 'required' not in response['content']['application/json']['schema']

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
        assert 'description' in responses['200']

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

    def test_list_response_body_generation(self):
        """Test that an array schema is returned for list views."""
        path = '/'
        method = 'GET'

        class ItemSerializer(serializers.Serializer):
            text = serializers.CharField()

        class View(generics.GenericAPIView):
            serializer_class = ItemSerializer

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        assert responses == {
            '200': {
                'description': '',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'array',
                            'items': {
                                'properties': {
                                    'text': {
                                        'type': 'string',
                                    },
                                },
                                'required': ['text'],
                            },
                        },
                    },
                },
            },
        }

    def test_paginated_list_response_body_generation(self):
        """Test that pagination properties are added for a paginated list view."""
        path = '/'
        method = 'GET'

        class Pagination(pagination.BasePagination):
            def get_paginated_response_schema(self, schema):
                return {
                    'type': 'object',
                    'item': schema,
                }

        class ItemSerializer(serializers.Serializer):
            text = serializers.CharField()

        class View(generics.GenericAPIView):
            serializer_class = ItemSerializer
            pagination_class = Pagination

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        assert responses == {
            '200': {
                'description': '',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'item': {
                                'type': 'array',
                                'items': {
                                    'properties': {
                                        'text': {
                                            'type': 'string',
                                        },
                                    },
                                    'required': ['text'],
                                },
                            },
                        },
                    },
                },
            },
        }

    def test_delete_response_body_generation(self):
        """Test that a view's delete method generates a proper response body schema."""
        path = '/{id}/'
        method = 'DELETE'

        class View(generics.DestroyAPIView):
            serializer_class = views.ExampleSerializer

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        assert responses == {
            '204': {
                'description': '',
            },
        }

    def test_parser_mapping(self):
        """Test that view's parsers are mapped to OA media types"""
        path = '/{id}/'
        method = 'POST'

        class View(generics.CreateAPIView):
            serializer_class = views.ExampleSerializer
            parser_classes = [JSONParser, MultiPartParser]

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        request_body = inspector._get_request_body(path, method)

        assert len(request_body['content'].keys()) == 2
        assert 'multipart/form-data' in request_body['content']
        assert 'application/json' in request_body['content']

    def test_renderer_mapping(self):
        """Test that view's renderers are mapped to OA media types"""
        path = '/{id}/'
        method = 'GET'

        class View(generics.CreateAPIView):
            serializer_class = views.ExampleSerializer
            renderer_classes = [JSONRenderer]

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        # TODO this should be changed once the multiple response
        # schema support is there
        success_response = responses['200']

        assert len(success_response['content'].keys()) == 1
        assert 'application/json' in success_response['content']

    def test_serializer_filefield(self):
        path = '/{id}/'
        method = 'POST'

        class ItemSerializer(serializers.Serializer):
            attachment = serializers.FileField()

        class View(generics.CreateAPIView):
            serializer_class = ItemSerializer

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        request_body = inspector._get_request_body(path, method)
        mp_media = request_body['content']['multipart/form-data']
        attachment = mp_media['schema']['properties']['attachment']
        assert attachment['format'] == 'binary'

    def test_retrieve_response_body_generation(self):
        """
        Test that a list of properties is returned for retrieve item views.

        Pagination properties should not be added as the view represents a single item.
        """
        path = '/{id}/'
        method = 'GET'

        class Pagination(pagination.BasePagination):
            def get_paginated_response_schema(self, schema):
                return {
                    'type': 'object',
                    'item': schema,
                }

        class ItemSerializer(serializers.Serializer):
            text = serializers.CharField()

        class View(generics.GenericAPIView):
            serializer_class = ItemSerializer
            pagination_class = Pagination

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        assert responses == {
            '200': {
                'description': '',
                'content': {
                    'application/json': {
                        'schema': {
                            'properties': {
                                'text': {
                                    'type': 'string',
                                },
                            },
                            'required': ['text'],
                        },
                    },
                },
            },
        }

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
        assert operationId == 'listExamples'

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

    def test_serializer_datefield(self):
        path = '/'
        method = 'GET'
        view = create_view(
            views.ExampleGenericAPIView,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        response_schema = responses['200']['content']['application/json']['schema']
        properties = response_schema['items']['properties']
        assert properties['date']['type'] == properties['datetime']['type'] == 'string'
        assert properties['date']['format'] == 'date'
        assert properties['datetime']['format'] == 'date-time'

    def test_serializer_hstorefield(self):
        path = '/'
        method = 'GET'
        view = create_view(
            views.ExampleGenericAPIView,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        response_schema = responses['200']['content']['application/json']['schema']
        properties = response_schema['items']['properties']
        assert properties['hstore']['type'] == 'object'

    def test_serializer_validators(self):
        path = '/'
        method = 'GET'
        view = create_view(
            views.ExampleValidatedAPIView,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector._get_responses(path, method)
        response_schema = responses['200']['content']['application/json']['schema']
        properties = response_schema['items']['properties']

        assert properties['integer']['type'] == 'integer'
        assert properties['integer']['maximum'] == 99
        assert properties['integer']['minimum'] == -11

        assert properties['string']['minLength'] == 2
        assert properties['string']['maxLength'] == 10

        assert properties['lst']['minItems'] == 2
        assert properties['lst']['maxItems'] == 10

        assert properties['regex']['pattern'] == r'[ABC]12{3}'
        assert properties['regex']['description'] == 'must have an A, B, or C followed by 1222'

        assert properties['decimal1']['type'] == 'number'
        assert properties['decimal1']['multipleOf'] == .01
        assert properties['decimal1']['maximum'] == 10000
        assert properties['decimal1']['minimum'] == -10000

        assert properties['decimal2']['type'] == 'number'
        assert properties['decimal2']['multipleOf'] == .0001

        assert properties['email']['type'] == 'string'
        assert properties['email']['format'] == 'email'
        assert properties['email']['default'] == 'foo@bar.com'

        assert properties['url']['type'] == 'string'
        assert properties['url']['nullable'] is True
        assert properties['url']['default'] == 'http://www.example.com'

        assert properties['uuid']['type'] == 'string'
        assert properties['uuid']['format'] == 'uuid'

        assert properties['ip4']['type'] == 'string'
        assert properties['ip4']['format'] == 'ipv4'

        assert properties['ip6']['type'] == 'string'
        assert properties['ip6']['format'] == 'ipv6'

        assert properties['ip']['type'] == 'string'
        assert 'format' not in properties['ip']


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

    def test_schema_information(self):
        """Construction of the top level dictionary."""
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns, title='My title', version='1.2.3', description='My description')

        request = create_request('/')
        schema = generator.get_schema(request=request)

        assert schema['info']['title'] == 'My title'
        assert schema['info']['version'] == '1.2.3'
        assert schema['info']['description'] == 'My description'

    def test_schema_information_empty(self):
        """Construction of the top level dictionary."""
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        assert schema['info']['title'] == ''
        assert schema['info']['version'] == ''
