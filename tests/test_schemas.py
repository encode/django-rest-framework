import unittest

from django.conf.urls import include, url
from django.test import TestCase, override_settings

from rest_framework import filters, pagination, permissions, serializers
from rest_framework.compat import coreapi
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIClient
from rest_framework.viewsets import ModelViewSet


class MockUser(object):
    def is_authenticated(self):
        return True


class ExamplePagination(pagination.PageNumberPagination):
    page_size = 100


class ExampleSerializer(serializers.Serializer):
    a = serializers.CharField(required=True)
    b = serializers.CharField(required=False)


class ExampleViewSet(ModelViewSet):
    pagination_class = ExamplePagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    serializer_class = ExampleSerializer


router = DefaultRouter(schema_title='Example API' if coreapi else None)
router.register('example', ExampleViewSet, base_name='example')
urlpatterns = [
    url(r'^', include(router.urls))
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
                'example': {
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
                'example': {
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
                            coreapi.Field('a', required=True, location='form'),
                            coreapi.Field('b', required=False, location='form')
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
                            coreapi.Field('a', required=True, location='form'),
                            coreapi.Field('b', required=False, location='form')
                        ]
                    ),
                    'partial_update': coreapi.Link(
                        url='/example/{pk}/',
                        action='patch',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('pk', required=True, location='path'),
                            coreapi.Field('a', required=False, location='form'),
                            coreapi.Field('b', required=False, location='form')
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
