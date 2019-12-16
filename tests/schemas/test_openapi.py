import pytest
from django.conf.urls import include, url
from django.db import models
from django.test import RequestFactory, TestCase, override_settings
from django.utils.translation import gettext_lazy as _

from rest_framework import (
    filters, generics, pagination, routers, serializers, viewsets
)
from rest_framework.compat import uritemplate
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.schemas.openapi import (
    AutoSchema, ComponentRegistry, SchemaGenerator
)

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
                assert inspector._map_field('GET', field) == mapping

    def test_lazy_string_field(self):
        class Serializer(serializers.Serializer):
            text = serializers.CharField(help_text=_('lazy string'))

        inspector = AutoSchema()

        data = inspector._map_serializer('GET', Serializer())
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
        inspector.init(ComponentRegistry())

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'listDocStringExamples',
            'description': 'A description of my GET operation.',
            'parameters': [],
            'responses': {
                '200': {
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'array',
                                'items': {
                                    'type': 'object',
                                    'description': 'Unspecified response body'
                                }
                            }
                        },
                    },
                    'description': ''
                },
            }
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
        inspector.init(ComponentRegistry())
        inspector.view = view

        operation = inspector.get_operation(path, method)
        assert operation == {
            'operationId': 'RetrieveDocStringExampleDetail',
            'description': 'A description of my GET operation.',
            'parameters': [
                {
                    'name': 'id',
                    'in': 'path',
                    'required': True,
                    'description': '',
                    'schema': {
                        'type': 'string'
                    }
                }
            ],
            'responses': {
                '200': {
                    'content': {
                        'application/json': {
                            'schema': {
                                'type': 'object',
                                'description': 'Unspecified response body'
                            }
                        }
                    },
                    'description': ''
                }
            }
        }

    def test_request_body(self):
        path = '/'
        method = 'POST'

        class ExampleSerializer(serializers.Serializer):
            text = serializers.CharField()
            read_only = serializers.CharField(read_only=True)

        class View(generics.CreateAPIView):
            serializer_class = ExampleSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)
        inspector.get_operation(path, method)

        schema = registry.schemas['Example']
        assert schema['required'] == ['text']
        assert schema['properties']['read_only']['readOnly'] is True

    def test_empty_required(self):
        path = '/'
        method = 'POST'

        class ExampleSerializer(serializers.Serializer):
            read_only = serializers.CharField(read_only=True)
            write_only = serializers.CharField(write_only=True, required=False)

        class View(generics.CreateAPIView):
            serializer_class = ExampleSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)
        inspector.get_operation(path, method)

        schema = registry.schemas['Example']
        # there should be no empty 'required' property, see #6834
        assert 'required' not in schema

    def test_empty_required_with_patch_method(self):
        path = '/'
        method = 'PATCH'

        class ExampleSerializer(serializers.Serializer):
            read_only = serializers.CharField(read_only=True)
            write_only = serializers.CharField(write_only=True, required=False)

        class View(generics.UpdateAPIView):
            serializer_class = ExampleSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)
        inspector.get_operation(path, method)

        schema = registry.schemas['PatchedExample']
        # there should be no empty 'required' property, see #6834
        assert 'required' not in schema
        for field_schema in schema['properties']:
            assert 'required' not in field_schema

    def test_response_body_generation(self):
        path = '/'
        method = 'POST'

        class ExampleSerializer(serializers.Serializer):
            text = serializers.CharField()
            write_only = serializers.CharField(write_only=True)

        class View(generics.CreateAPIView):
            serializer_class = ExampleSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)

        operation = inspector.get_operation(path, method)

        assert operation['responses'] == {
            '200': {
                'content': {
                    'application/json': {
                        'schema': {'$ref': '#/components/schemas/Example'}
                    }
                },
                'description': ''
            }
        }
        assert sorted(registry.schemas['Example']['required']) == ['text', 'write_only']
        assert sorted(registry.schemas['Example']['properties'].keys()) == ['text', 'write_only']

    def test_response_body_nested_serializer(self):
        path = '/'
        method = 'POST'

        class NestedSerializer(serializers.Serializer):
            number = serializers.IntegerField()

        class ExampleSerializer(serializers.Serializer):
            text = serializers.CharField()
            nested = NestedSerializer()

        class View(generics.CreateAPIView):
            serializer_class = ExampleSerializer

        view = create_view(
            View,
            method,
            create_request(path),
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)
        inspector.get_operation(path, method)
        example_schema = registry.schemas['Example']
        nested_schema = registry.schemas['Nested']

        assert sorted(example_schema['required']) == ['nested', 'text']
        assert sorted(example_schema['properties'].keys()) == ['nested', 'text']
        assert example_schema['properties']['nested']['type'] == 'object'
        assert sorted(nested_schema['properties'].keys()) == ['number']
        assert nested_schema['required'] == ['number']

    def test_list_response_body_generation(self):
        """Test that an array schema is returned for list views."""
        path = '/'
        method = 'GET'

        class ItemSerializer(serializers.Serializer):
            text = serializers.CharField()

        class View(generics.ListAPIView):
            serializer_class = ItemSerializer

        view = create_view(
            View,
            method,
            create_request(path),
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)

        operation = inspector.get_operation(path, method)

        assert operation['responses'] == {
            '200': {
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'array',
                            'items': {'$ref': '#/components/schemas/Item'},
                        }
                    }
                },
                'description': ''
            }
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

        class View(generics.ListAPIView):
            serializer_class = ItemSerializer
            pagination_class = Pagination

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(ComponentRegistry())

        operation = inspector.get_operation(path, method)
        assert operation['responses'] == {
            '200': {
                'description': '',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'object',
                            'item': {
                                'type': 'array',
                                'items': {'$ref': '#/components/schemas/Item'},
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
        inspector.init(ComponentRegistry())

        operation = inspector.get_operation(path, method)
        assert operation['responses'] == {
            '204': {
                'description': 'No response body',
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
        inspector.init(ComponentRegistry())

        operation = inspector.get_operation(path, method)
        content = operation['requestBody']['content']
        assert len(content.keys()) == 2
        assert 'multipart/form-data' in content
        assert 'application/json' in content

    def test_renderer_mapping(self):
        """Test that view's renderers are mapped to OA media types"""
        path = '/{id}/'
        method = 'GET'

        class View(generics.ListCreateAPIView):
            serializer_class = views.ExampleSerializer
            renderer_classes = [JSONRenderer]

        view = create_view(
            View,
            method,
            create_request(path),
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)

        operation = inspector.get_operation(path, method)
        # TODO this should be changed once the multiple response
        # schema support is there
        success_response = operation['responses']['200']

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
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)

        operation = inspector.get_operation(path, method)

        assert 'multipart/form-data' in operation['requestBody']['content']
        assert registry.schemas['Item']['properties']['attachment']['format'] == 'binary'

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

        class View(generics.RetrieveAPIView):
            serializer_class = ItemSerializer
            pagination_class = Pagination

        view = create_view(
            View,
            method,
            create_request(path),
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)

        operation = inspector.get_operation(path, method)

        assert operation['responses'] == {
            '200': {
                'content': {
                    'application/json': {
                        'schema': {'$ref': '#/components/schemas/Item'}
                    }
                },
                'description': ''
            }
        }
        assert registry.schemas['Item'] == {
            'properties': {
                'text': {
                    'type': 'string',
                },
            },
            'required': ['text'],
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
        inspector.init(ComponentRegistry())

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
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)
        inspector.get_operation(path, method)

        properties = registry.schemas['Example']['properties']
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
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)
        inspector.get_operation(path, method)

        properties = registry.schemas['Example']['properties']
        assert properties['hstore']['type'] == 'object'

    def test_serializer_callable_default(self):
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
        assert 'default' not in properties['uuid_field']

    def test_serializer_validators(self):
        path = '/'
        method = 'GET'
        view = create_view(
            views.ExampleValidatedAPIView,
            method,
            create_request(path),
        )
        registry = ComponentRegistry()
        inspector = AutoSchema()
        inspector.view = view
        inspector.init(registry)
        inspector.get_operation(path, method)

        properties = registry.schemas['ExampleValidated']['properties']

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

    def test_modelviewset(self):
        class ExampleModel(models.Model):
            text = models.TextField()

        class ExampleSerializer(serializers.ModelSerializer):
            class Meta:
                model = ExampleModel
                fields = ['id', 'text']

        class ExampleViewSet(viewsets.ModelViewSet):
            serializer_class = ExampleSerializer
            queryset = ExampleModel.objects.none()

        router = routers.DefaultRouter()
        router.register(r'example', ExampleViewSet)

        generator = SchemaGenerator(patterns=[
            url(r'api/', include(router.urls))
        ])
        generator._initialise_endpoints()

        schema = generator.get_schema(request=None, public=True)

        assert sorted(schema['paths']['/api/example/'].keys()) == ['get', 'post']
        assert sorted(schema['paths']['/api/example/{id}/'].keys()) == ['delete', 'get', 'patch', 'put']
        assert sorted(schema['components']['schemas'].keys()) == ['Example', 'PatchedExample']
        # TODO do more checks


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

        paths = generator.parse()

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

        paths = generator.parse()

        assert '/v1/example/' in paths
        assert '/v1/example/{id}/' in paths

    def test_mount_url_prefixed_to_paths(self):
        patterns = [
            url(r'^example/?$', views.ExampleListView.as_view()),
            url(r'^example/{pk}/?$', views.ExampleDetailView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns, url='/api')
        generator._initialise_endpoints()

        paths = generator.parse()

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
