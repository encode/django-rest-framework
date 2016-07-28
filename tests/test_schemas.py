import unittest

from django.conf.urls import include, url
from django.test import TestCase, override_settings

from rest_framework import filters, pagination, permissions, serializers
from rest_framework.compat import coreapi
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework.schemas import SchemaGenerator
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet


class MockUser(object):
    def is_authenticated(self):
        return True


class ExamplePagination(pagination.PageNumberPagination):
    page_size = 100


class ExampleSerializer(serializers.Serializer):
    a = serializers.CharField(required=True, help_text='About a')
    b = serializers.CharField(required=False, help_text='About b')


class ExampleViewSet(ModelViewSet):
    pagination_class = ExamplePagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    serializer_class = ExampleSerializer


class ExampleView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    path_fields_descriptions = {
        'example_id': 'Description of example_id path parameter',
    }

    def get(self, request, *args, **kwargs):
        """get documentation"""
        return Response()

    def post(self, request, *args, **kwargs):
        return Response()


router = DefaultRouter(schema_title='Example API' if coreapi else None)
router.register('example', ExampleViewSet, base_name='example')
urlpatterns = [
    url(r'^', include(router.urls))
]
urlpatterns2 = [
    url(r'^example-view/$', ExampleView.as_view(), name='example-view')
]


router = SimpleRouter()
router.register('example', ExampleViewSet, base_name='example')
urlpatterns3 = [
    url(r'^', include(router.urls)),
    url(r'^(?P<example_id>\w+)/example-view/$', ExampleView.as_view(), name='example-view')
]


@unittest.skipUnless(coreapi, 'coreapi is not installed')
@override_settings(ROOT_URLCONF='tests.test_schemas')
class TestRouterGeneratedSchema(TestCase):
    def test_anonymous_request(self):
        client = APIClient()
        response = client.get('/', HTTP_ACCEPT='application/vnd.coreapi+json')
        self.assertEqual(response.status_code, 200)
        expected = coreapi.Document(
            url='',
            title='Example API',
            content={
                'Example': {
                    'list': coreapi.Link(
                        url='/example/',
                        action='get',
                        fields=[
                            coreapi.Field('page', required=False, location='query'),
                            coreapi.Field('ordering', required=False, location='query')
                        ]
                    ),
                    'retrieve': coreapi.Link(
                        url='/example/{pk}/',
                        action='get',
                        fields=[
                            coreapi.Field('pk', required=True, location='path')
                        ]
                    )
                }
            }
        )
        self.assertEqual(response.data, expected)

    def test_authenticated_request(self):
        client = APIClient()
        client.force_authenticate(MockUser())
        response = client.get('/', HTTP_ACCEPT='application/vnd.coreapi+json')
        self.assertEqual(response.status_code, 200)
        expected = coreapi.Document(
            url='',
            title='Example API',
            content={
                'Example': {
                    'list': coreapi.Link(
                        url='/example/',
                        action='get',
                        fields=[
                            coreapi.Field('page', required=False, location='query'),
                            coreapi.Field('ordering', required=False, location='query')
                        ]
                    ),
                    'create': coreapi.Link(
                        url='/example/',
                        action='post',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('a', required=True, location='form', description='About a'),
                            coreapi.Field('b', required=False, location='form', description='About b')
                        ]
                    ),
                    'retrieve': coreapi.Link(
                        url='/example/{pk}/',
                        action='get',
                        fields=[
                            coreapi.Field('pk', required=True, location='path')
                        ]
                    ),
                    'update': coreapi.Link(
                        url='/example/{pk}/',
                        action='put',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('pk', required=True, location='path'),
                            coreapi.Field('a', required=True, location='form', description='About a'),
                            coreapi.Field('b', required=False, location='form', description='About b')
                        ]
                    ),
                    'partial_update': coreapi.Link(
                        url='/example/{pk}/',
                        action='patch',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('pk', required=True, location='path'),
                            coreapi.Field('a', required=False, location='form', description='About a'),
                            coreapi.Field('b', required=False, location='form', description='About b')
                        ]
                    ),
                    'destroy': coreapi.Link(
                        url='/example/{pk}/',
                        action='delete',
                        fields=[
                            coreapi.Field('pk', required=True, location='path')
                        ]
                    )
                }
            }
        )
        self.assertEqual(response.data, expected)


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaGenerator(TestCase):
    def test_view(self):
        schema_generator = SchemaGenerator(title='Test View', patterns=urlpatterns2)
        schema = schema_generator.get_schema()
        expected = coreapi.Document(
            url='',
            title='Test View',
            content={
                'Example-view': {
                    'create': coreapi.Link(
                        url='/example-view/',
                        action='post',
                        fields=[]
                    ),
                    'read': coreapi.Link(
                        url='/example-view/',
                        action='get',
                        description='get documentation',
                        fields=[]
                    )
                }
            }
        )
        self.assertEquals(schema, expected)


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaAndSubSchemaGenerator(TestCase):
    def test_view(self):
        schema_generator = SchemaGenerator(title='Test View', patterns=urlpatterns3)
        schema = schema_generator.get_schema()
        expected = coreapi.Document(
            url='',
            title='Test View',
            content={
                'Example': {
                    'list': coreapi.Link(
                        url='/example/',
                        action='get',
                        fields=[
                            coreapi.Field('page', required=False, location='query'),
                            coreapi.Field('ordering', required=False, location='query')
                        ]
                    ),
                    'create': coreapi.Link(
                        url='/example/',
                        action='post',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('a', required=True, location='form', description='About a'),
                            coreapi.Field('b', required=False, location='form', description='About b')
                        ]
                    ),
                    'retrieve': coreapi.Link(
                        url='/example/{pk}/',
                        action='get',
                        fields=[
                            coreapi.Field('pk', required=True, location='path')
                        ]
                    ),
                    'update': coreapi.Link(
                        url='/example/{pk}/',
                        action='put',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('pk', required=True, location='path'),
                            coreapi.Field('a', required=True, location='form', description='About a'),
                            coreapi.Field('b', required=False, location='form', description='About b')
                        ]
                    ),
                    'partial_update': coreapi.Link(
                        url='/example/{pk}/',
                        action='patch',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('pk', required=True, location='path'),
                            coreapi.Field('a', required=False, location='form', description='About a'),
                            coreapi.Field('b', required=False, location='form', description='About b')
                        ]
                    ),
                    'destroy': coreapi.Link(
                        url='/example/{pk}/',
                        action='delete',
                        fields=[
                            coreapi.Field('pk', required=True, location='path')
                        ]
                    )
                },
                'Example-view': {
                    'create': coreapi.Link(
                        url='/{example_id}/example-view/',
                        action='post',
                        fields=[
                            coreapi.Field('example_id', required=True, location='path', description='Description of example_id path parameter')
                        ]
                    ),
                    'read': coreapi.Link(
                        url='/{example_id}/example-view/',
                        action='get',
                        description='get documentation',
                        fields=[
                            coreapi.Field('example_id', required=True, location='path', description='Description of example_id path parameter')
                        ]
                    )
                },
            }
        )
        self.assertEquals(schema, expected)
