import uuid
import warnings

import pytest
from django.test import RequestFactory, TestCase, override_settings
from django.urls import path
from django.utils.translation import gettext_lazy as _

from rest_framework import filters, generics, pagination, routers, serializers
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.compat import uritemplate
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.renderers import (
    BaseRenderer, BrowsableAPIRenderer, JSONRenderer, OpenAPIRenderer
)
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
        uuid1 = uuid.uuid4()
        uuid2 = uuid.uuid4()
        inspector = AutoSchema()
        cases = [
            (serializers.ListField(), {'items': {}, 'type': 'array'}),
            (serializers.ListField(child=serializers.BooleanField()), {'items': {'type': 'boolean'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.FloatField()), {'items': {'type': 'number'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.CharField()), {'items': {'type': 'string'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.IntegerField(max_value=4294967295)),
             {'items': {'type': 'integer', 'maximum': 4294967295, 'format': 'int64'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.ChoiceField(choices=[('a', 'Choice A'), ('b', 'Choice B')])),
             {'items': {'enum': ['a', 'b'], 'type': 'string'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.ChoiceField(choices=[(1, 'One'), (2, 'Two')])),
             {'items': {'enum': [1, 2], 'type': 'integer'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.ChoiceField(choices=[(1.1, 'First'), (2.2, 'Second')])),
             {'items': {'enum': [1.1, 2.2], 'type': 'number'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.ChoiceField(choices=[(True, 'true'), (False, 'false')])),
             {'items': {'enum': [True, False], 'type': 'boolean'}, 'type': 'array'}),
            (serializers.ListField(child=serializers.ChoiceField(choices=[(uuid1, 'uuid1'), (uuid2, 'uuid2')])),
             {'items': {'enum': [uuid1, uuid2]}, 'type': 'array'}),
            (serializers.ListField(child=serializers.ChoiceField(choices=[(1, 'One'), ('a', 'Choice A')])),
             {'items': {'enum': [1, 'a']}, 'type': 'array'}),
            (serializers.ListField(child=serializers.ChoiceField(choices=[
                (1, 'One'), ('a', 'Choice A'), (1.1, 'First'), (1.1, 'First'), (1, 'One'), ('a', 'Choice A'), (1, 'One')
            ])),
                {'items': {'enum': [1, 'a', 1.1]}, 'type': 'array'}),
            (serializers.ListField(child=serializers.ChoiceField(choices=[
                (1, 'One'), (2, 'Two'), (3, 'Three'), (2, 'Two'), (3, 'Three'), (1, 'One'),
            ])),
                {'items': {'enum': [1, 2, 3], 'type': 'integer'}, 'type': 'array'}),
            (serializers.IntegerField(min_value=2147483648),
             {'type': 'integer', 'minimum': 2147483648, 'format': 'int64'}),
        ]
        for field, mapping in cases:
            with self.subTest(field=field):
                assert inspector.map_field(field) == mapping

    def test_lazy_string_field(self):
        class ItemSerializer(serializers.Serializer):
            text = serializers.CharField(help_text=_('lazy string'))

        inspector = AutoSchema()

        data = inspector.map_serializer(ItemSerializer())
        assert isinstance(data['properties']['text']['description'], str), "description must be str"

    def test_boolean_default_field(self):
        class Serializer(serializers.Serializer):
            default_true = serializers.BooleanField(default=True)
            default_false = serializers.BooleanField(default=False)
            without_default = serializers.BooleanField()

        inspector = AutoSchema()

        data = inspector.map_serializer(Serializer())
        assert data['properties']['default_true']['default'] is True, "default must be true"
        assert data['properties']['default_false']['default'] is False, "default must be false"
        assert 'default' not in data['properties']['without_default'], "default must not be defined"


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
            'tags': ['example'],
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
            'operationId': 'retrieveDocStringExampleDetail',
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
            'tags': ['example'],
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

        class ItemSerializer(serializers.Serializer):
            text = serializers.CharField()
            read_only = serializers.CharField(read_only=True)

        class View(generics.GenericAPIView):
            serializer_class = ItemSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        inspector = AutoSchema()
        inspector.view = view

        request_body = inspector.get_request_body(path, method)
        print(request_body)
        assert request_body['content']['application/json']['schema']['$ref'] == '#/components/schemas/Item'

        components = inspector.get_components(path, method)
        assert components['Item']['required'] == ['text']
        assert sorted(list(components['Item']['properties'].keys())) == ['read_only', 'text']

    def test_invalid_serializer_class_name(self):
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

        serializer = inspector.get_serializer(path, method)

        with pytest.raises(Exception) as exc:
            inspector.get_component_name(serializer)
        assert "is an invalid class name for schema generation" in str(exc.value)

    def test_empty_required(self):
        path = '/'
        method = 'POST'

        class ItemSerializer(serializers.Serializer):
            read_only = serializers.CharField(read_only=True)
            write_only = serializers.CharField(write_only=True, required=False)

        class View(generics.GenericAPIView):
            serializer_class = ItemSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        inspector = AutoSchema()
        inspector.view = view

        components = inspector.get_components(path, method)
        component = components['Item']
        # there should be no empty 'required' property, see #6834
        assert 'required' not in component

        for response in inspector.get_responses(path, method).values():
            assert 'required' not in component

    def test_empty_required_with_patch_method(self):
        path = '/'
        method = 'PATCH'

        class ItemSerializer(serializers.Serializer):
            read_only = serializers.CharField(read_only=True)
            write_only = serializers.CharField(write_only=True, required=False)

        class View(generics.GenericAPIView):
            serializer_class = ItemSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        inspector = AutoSchema()
        inspector.view = view

        components = inspector.get_components(path, method)
        component = components['Item']
        # there should be no empty 'required' property, see #6834
        assert 'required' not in component
        for response in inspector.get_responses(path, method).values():
            assert 'required' not in component

    def test_response_body_generation(self):
        path = '/'
        method = 'POST'

        class ItemSerializer(serializers.Serializer):
            text = serializers.CharField()
            write_only = serializers.CharField(write_only=True)

        class View(generics.GenericAPIView):
            serializer_class = ItemSerializer

        view = create_view(
            View,
            method,
            create_request(path)
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector.get_responses(path, method)
        assert responses['201']['content']['application/json']['schema']['$ref'] == '#/components/schemas/Item'

        components = inspector.get_components(path, method)
        assert sorted(components['Item']['required']) == ['text', 'write_only']
        assert sorted(list(components['Item']['properties'].keys())) == ['text', 'write_only']
        assert 'description' in responses['201']

    def test_response_body_nested_serializer(self):
        path = '/'
        method = 'POST'

        class NestedSerializer(serializers.Serializer):
            number = serializers.IntegerField()

        class ItemSerializer(serializers.Serializer):
            text = serializers.CharField()
            nested = NestedSerializer()

        class View(generics.GenericAPIView):
            serializer_class = ItemSerializer

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector.get_responses(path, method)
        assert responses['201']['content']['application/json']['schema']['$ref'] == '#/components/schemas/Item'
        components = inspector.get_components(path, method)
        assert components['Item']

        schema = components['Item']
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

        responses = inspector.get_responses(path, method)
        assert responses == {
            '200': {
                'description': '',
                'content': {
                    'application/json': {
                        'schema': {
                            'type': 'array',
                            'items': {
                                '$ref': '#/components/schemas/Item'
                            },
                        },
                    },
                },
            },
        }
        components = inspector.get_components(path, method)
        assert components == {
            'Item': {
                'type': 'object',
                'properties': {
                    'text': {
                        'type': 'string',
                    },
                },
                'required': ['text'],
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

        responses = inspector.get_responses(path, method)
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
                                    '$ref': '#/components/schemas/Item'
                                },
                            },
                        },
                    },
                },
            },
        }
        components = inspector.get_components(path, method)
        assert components == {
            'Item': {
                'type': 'object',
                'properties': {
                    'text': {
                        'type': 'string',
                    },
                },
                'required': ['text'],
            }
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

        responses = inspector.get_responses(path, method)
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

        request_body = inspector.get_request_body(path, method)

        assert len(request_body['content'].keys()) == 2
        assert 'multipart/form-data' in request_body['content']
        assert 'application/json' in request_body['content']

    def test_renderer_mapping(self):
        """Test that view's renderers are mapped to OA media types"""
        path = '/{id}/'
        method = 'GET'

        class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
            media_type = 'image/jpeg'  # that's a wild API renderer

        class TextRenderer(BaseRenderer):
            media_type = 'text/plain'
            format = 'text'

        class View(generics.CreateAPIView):
            serializer_class = views.ExampleSerializer
            renderer_classes = [JSONRenderer, TextRenderer, BrowsableAPIRenderer, CustomBrowsableAPIRenderer]

        view = create_view(
            View,
            method,
            create_request(path),
        )
        inspector = AutoSchema()
        inspector.view = view

        responses = inspector.get_responses(path, method)
        # TODO this should be changed once the multiple response
        # schema support is there
        success_response = responses['200']

        # Check that the API renderers aren't included, but custom renderers are
        assert set(success_response['content']) == {'application/json', 'text/plain'}

    def test_openapi_yaml_rendering_without_aliases(self):
        renderer = OpenAPIRenderer()

        reused_object = {'test': 'test'}
        data = {
            'o1': reused_object,
            'o2': reused_object,
        }
        assert (
            renderer.render(data) == b'o1:\n  test: test\no2:\n  test: test\n' or
            renderer.render(data) == b'o2:\n  test: test\no1:\n  test: test\n'  # py <= 3.5
        )

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

        components = inspector.get_components(path, method)
        component = components['Item']
        properties = component['properties']
        assert properties['attachment']['format'] == 'binary'

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

        responses = inspector.get_responses(path, method)
        assert responses == {
            '200': {
                'description': '',
                'content': {
                    'application/json': {
                        'schema': {
                            '$ref': '#/components/schemas/Item'
                        },
                    },
                },
            },
        }

        components = inspector.get_components(path, method)
        assert components == {
            'Item': {
                'type': 'object',
                'properties': {
                    'text': {
                        'type': 'string',
                    },
                },
                'required': ['text'],
            }
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

        operationId = inspector.get_operation_id(path, method)
        assert operationId == 'listExamples'

    def test_operation_id_custom_operation_id_base(self):
        path = '/'
        method = 'GET'

        view = create_view(
            views.ExampleGenericAPIView,
            method,
            create_request(path),
        )
        inspector = AutoSchema(operation_id_base="Ulysse")
        inspector.view = view

        operationId = inspector.get_operation_id(path, method)
        assert operationId == 'listUlysses'

    def test_operation_id_custom_name(self):
        path = '/'
        method = 'GET'

        view = create_view(
            views.ExampleGenericAPIView,
            method,
            create_request(path),
        )
        inspector = AutoSchema(operation_id_base='Ulysse')
        inspector.view = view

        operationId = inspector.get_operation_id(path, method)
        assert operationId == 'listUlysses'

    def test_operation_id_override_get(self):
        class CustomSchema(AutoSchema):
            def get_operation_id(self, path, method):
                return 'myCustomOperationId'

        path = '/'
        method = 'GET'
        view = create_view(
            views.ExampleGenericAPIView,
            method,
            create_request(path),
        )
        inspector = CustomSchema()
        inspector.view = view

        operationId = inspector.get_operation_id(path, method)
        assert operationId == 'myCustomOperationId'

    def test_operation_id_override_base(self):
        class CustomSchema(AutoSchema):
            def get_operation_id_base(self, path, method, action):
                return 'Item'

        path = '/'
        method = 'GET'
        view = create_view(
            views.ExampleGenericAPIView,
            method,
            create_request(path),
        )
        inspector = CustomSchema()
        inspector.view = view

        operationId = inspector.get_operation_id(path, method)
        assert operationId == 'listItem'

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

    def test_duplicate_operation_id(self):
        patterns = [
            path('duplicate1/', views.ExampleOperationIdDuplicate1.as_view()),
            path('duplicate2/', views.ExampleOperationIdDuplicate2.as_view()),
        ]

        generator = SchemaGenerator(patterns=patterns)
        request = create_request('/')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            generator.get_schema(request=request)

            assert len(w) == 1
            assert issubclass(w[-1].category, UserWarning)
            print(str(w[-1].message))
            assert 'You have a duplicated operationId' in str(w[-1].message)

    def test_operation_id_viewset(self):
        router = routers.SimpleRouter()
        router.register('account', views.ExampleViewSet, basename="account")
        urlpatterns = router.urls

        generator = SchemaGenerator(patterns=urlpatterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)
        print(schema)
        assert schema['paths']['/account/']['get']['operationId'] == 'listExampleViewSets'
        assert schema['paths']['/account/']['post']['operationId'] == 'createExampleViewSet'
        assert schema['paths']['/account/{id}/']['get']['operationId'] == 'retrieveExampleViewSet'
        assert schema['paths']['/account/{id}/']['put']['operationId'] == 'updateExampleViewSet'
        assert schema['paths']['/account/{id}/']['patch']['operationId'] == 'partialUpdateExampleViewSet'
        assert schema['paths']['/account/{id}/']['delete']['operationId'] == 'destroyExampleViewSet'

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

        components = inspector.get_components(path, method)
        component = components['Example']
        properties = component['properties']
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

        components = inspector.get_components(path, method)
        component = components['Example']
        properties = component['properties']
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

        components = inspector.get_components(path, method)
        component = components['Example']
        properties = component['properties']
        assert 'default' not in properties['uuid_field']

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

        components = inspector.get_components(path, method)
        component = components['ExampleValidated']
        properties = component['properties']

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

        assert properties['decimal3'] == {
            'type': 'string', 'format': 'decimal', 'maximum': 1000000, 'minimum': -1000000, 'multipleOf': 0.01
        }
        assert properties['decimal4'] == {
            'type': 'string', 'format': 'decimal', 'maximum': 1000000, 'minimum': -1000000, 'multipleOf': 0.01
        }
        assert properties['decimal5'] == {
            'type': 'string', 'format': 'decimal', 'maximum': 10000, 'minimum': -10000, 'multipleOf': 0.01
        }

        assert properties['email']['type'] == 'string'
        assert properties['email']['format'] == 'email'
        assert properties['email']['default'] == 'foo@bar.com'

        assert properties['url']['type'] == 'string'
        assert properties['url']['nullable'] is True
        assert properties['url']['default'] == 'http://www.example.com'
        assert '\\Z' not in properties['url']['pattern']

        assert properties['uuid']['type'] == 'string'
        assert properties['uuid']['format'] == 'uuid'

        assert properties['ip4']['type'] == 'string'
        assert properties['ip4']['format'] == 'ipv4'

        assert properties['ip6']['type'] == 'string'
        assert properties['ip6']['format'] == 'ipv6'

        assert properties['ip']['type'] == 'string'
        assert 'format' not in properties['ip']

    def test_overridden_tags(self):
        class ExampleStringTagsViewSet(views.ExampleGenericAPIView):
            schema = AutoSchema(tags=['example1', 'example2'])

        url_patterns = [
            path('test/', ExampleStringTagsViewSet.as_view()),
        ]
        generator = SchemaGenerator(patterns=url_patterns)
        schema = generator.get_schema(request=create_request('/'))
        assert schema['paths']['/test/']['get']['tags'] == ['example1', 'example2']

    def test_overridden_get_tags_method(self):
        class MySchema(AutoSchema):
            def get_tags(self, path, method):
                if path.endswith('/new/'):
                    tags = ['tag1', 'tag2']
                elif path.endswith('/old/'):
                    tags = ['tag2', 'tag3']
                else:
                    tags = ['tag4', 'tag5']

                return tags

        class ExampleStringTagsViewSet(views.ExampleGenericViewSet):
            schema = MySchema()

        router = routers.SimpleRouter()
        router.register('example', ExampleStringTagsViewSet, basename="example")
        generator = SchemaGenerator(patterns=router.urls)
        schema = generator.get_schema(request=create_request('/'))
        assert schema['paths']['/example/new/']['get']['tags'] == ['tag1', 'tag2']
        assert schema['paths']['/example/old/']['get']['tags'] == ['tag2', 'tag3']

    def test_auto_generated_apiview_tags(self):
        class RestaurantAPIView(views.ExampleGenericAPIView):
            schema = AutoSchema(operation_id_base="restaurant")
            pass

        class BranchAPIView(views.ExampleGenericAPIView):
            pass

        url_patterns = [
            path('any-dash_underscore/', RestaurantAPIView.as_view()),
            path('restaurants/branches/', BranchAPIView.as_view())
        ]
        generator = SchemaGenerator(patterns=url_patterns)
        schema = generator.get_schema(request=create_request('/'))
        assert schema['paths']['/any-dash_underscore/']['get']['tags'] == ['any-dash-underscore']
        assert schema['paths']['/restaurants/branches/']['get']['tags'] == ['restaurants']


@pytest.mark.skipif(uritemplate is None, reason='uritemplate not installed.')
@override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.openapi.AutoSchema'})
class TestGenerator(TestCase):

    def test_override_settings(self):
        assert isinstance(views.ExampleListView.schema, AutoSchema)

    def test_paths_construction(self):
        """Construction of the `paths` key."""
        patterns = [
            path('example/', views.ExampleListView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)
        generator._initialise_endpoints()

        paths = generator.get_schema()["paths"]

        assert '/example/' in paths
        example_operations = paths['/example/']
        assert len(example_operations) == 2
        assert 'get' in example_operations
        assert 'post' in example_operations

    def test_prefixed_paths_construction(self):
        """Construction of the `paths` key maintains a common prefix."""
        patterns = [
            path('v1/example/', views.ExampleListView.as_view()),
            path('v1/example/{pk}/', views.ExampleDetailView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)
        generator._initialise_endpoints()

        paths = generator.get_schema()["paths"]

        assert '/v1/example/' in paths
        assert '/v1/example/{id}/' in paths

    def test_mount_url_prefixed_to_paths(self):
        patterns = [
            path('example/', views.ExampleListView.as_view()),
            path('example/{pk}/', views.ExampleDetailView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns, url='/api')
        generator._initialise_endpoints()

        paths = generator.get_schema()["paths"]

        assert '/api/example/' in paths
        assert '/api/example/{id}/' in paths

    def test_schema_construction(self):
        """Construction of the top level dictionary."""
        patterns = [
            path('example/', views.ExampleListView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        assert 'openapi' in schema
        assert 'paths' in schema

    def test_schema_with_no_paths(self):
        patterns = []
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        assert schema['paths'] == {}

    def test_schema_information(self):
        """Construction of the top level dictionary."""
        patterns = [
            path('example/', views.ExampleListView.as_view()),
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
            path('example/', views.ExampleListView.as_view()),
        ]
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        assert schema['info']['title'] == ''
        assert schema['info']['version'] == ''

    def test_serializer_model(self):
        """Construction of the top level dictionary."""
        patterns = [
            path('example/', views.ExampleGenericAPIViewModel.as_view()),
        ]

        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        print(schema)

        assert 'components' in schema
        assert 'schemas' in schema['components']
        assert 'ExampleModel' in schema['components']['schemas']

    def test_authtoken_serializer(self):
        patterns = [
            path('api-token-auth/', obtain_auth_token)
        ]
        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        print(schema)

        route = schema['paths']['/api-token-auth/']['post']
        body_schema = route['requestBody']['content']['application/json']['schema']

        assert body_schema == {
            '$ref': '#/components/schemas/AuthToken'
        }
        assert schema['components']['schemas']['AuthToken'] == {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'writeOnly': True},
                'password': {'type': 'string', 'writeOnly': True},
                'token': {'type': 'string', 'readOnly': True},
            },
            'required': ['username', 'password']
        }

    def test_component_name(self):
        patterns = [
            path('example/', views.ExampleAutoSchemaComponentName.as_view()),
        ]

        generator = SchemaGenerator(patterns=patterns)

        request = create_request('/')
        schema = generator.get_schema(request=request)

        print(schema)
        assert 'components' in schema
        assert 'schemas' in schema['components']
        assert 'Ulysses' in schema['components']['schemas']

    def test_duplicate_component_name(self):
        patterns = [
            path('duplicate1/', views.ExampleAutoSchemaDuplicate1.as_view()),
            path('duplicate2/', views.ExampleAutoSchemaDuplicate2.as_view()),
        ]

        generator = SchemaGenerator(patterns=patterns)
        request = create_request('/')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            schema = generator.get_schema(request=request)

            assert len(w) == 1
            assert issubclass(w[-1].category, UserWarning)
            assert 'has been overriden with a different value.' in str(w[-1].message)

        assert 'components' in schema
        assert 'schemas' in schema['components']
        assert 'Duplicate' in schema['components']['schemas']

    def test_component_should_not_be_generated_for_delete_method(self):
        class ExampleView(generics.DestroyAPIView):
            schema = AutoSchema(operation_id_base='example')

        url_patterns = [
            path('example/', ExampleView.as_view()),
        ]
        generator = SchemaGenerator(patterns=url_patterns)
        schema = generator.get_schema(request=create_request('/'))
        assert 'components' not in schema
        assert 'content' not in schema['paths']['/example/']['delete']['responses']['204']
