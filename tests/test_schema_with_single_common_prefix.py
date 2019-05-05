import unittest

from django.conf.urls import include, url

from django.test import TestCase, override_settings

from rest_framework import serializers
from rest_framework.compat import coreapi
from rest_framework.decorators import action
from rest_framework.routers import SimpleRouter
from rest_framework.schemas import get_schema_view
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.viewsets import GenericViewSet

factory = APIRequestFactory()


class MockUser:
    def is_authenticated(self):
        return True


class ExampleSerializer(serializers.Serializer):
    a = serializers.CharField(required=True, help_text='A field description')
    b = serializers.CharField(required=False)
    read_only = serializers.CharField(read_only=True)
    hidden = serializers.HiddenField(default='hello')


class ExampleViewSet(GenericViewSet):
    serializer_class = ExampleSerializer

    @action(['GET'], detail=False)
    def test1(self):
        return Response({})

    @action(['GET'], detail=False)
    def test2(self):
        return Response({})


if coreapi:
    schema_view = get_schema_view(title='Example API')
else:
    def schema_view(request):
        pass

router = SimpleRouter()
router.register('example', ExampleViewSet, basename='example')
urlpatterns = [
    url(r'^$', schema_view),
    url(r'^example/', include(router.urls))
]


@unittest.skipUnless(coreapi, 'coreapi is not installed')
@override_settings(ROOT_URLCONF='tests.test_schema_with_single_common_prefix')
class AnotherTestRouterGeneratedSchema(TestCase):
    def test_anonymous_request(self):
        client = APIClient()
        response = client.get('/', HTTP_ACCEPT='application/coreapi+json')
        assert response.status_code == 200
        expected = coreapi.Document(
            url='http://testserver/',
            title='Example API',
            content={
                'test1': {
                    'test1': coreapi.Link(
                        url='/example/example/test1/',
                        action='get'
                    )
                },
                'test2': {
                    'test2': coreapi.Link(
                        url='/example/example/test2/',
                        action='get'
                    )
                }
            }
        )
        assert response.data == expected

    def test_authenticated_request(self):
        client = APIClient()
        client.force_authenticate(MockUser())
        response = client.get('/', HTTP_ACCEPT='application/coreapi+json')
        assert response.status_code == 200

        expected = coreapi.Document(
            url='http://testserver/',
            title='Example API',
            content={
                'test1': {
                    'test1': coreapi.Link(
                        url='/example/example/test1/',
                        action='get'
                    )
                },
                'test2': {
                    'test2': coreapi.Link(
                        url='/example/example/test2/',
                        action='get'
                    )
                }
            }
        )
        assert response.data == expected
