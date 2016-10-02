import unittest

from django.conf.urls import include, url
from django.test import TestCase, override_settings

from rest_framework import filters, pagination, permissions, serializers
from rest_framework.compat import coreapi
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import SchemaGenerator
from rest_framework.test import APIClient
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet


class MockUser(object):
    def is_authenticated(self):
        return True


class MockCoreapiObject(object):
    def __eq__(self, value):
        return True


class ExamplePagination(pagination.PageNumberPagination):
    page_size = 100


class ExampleSerializer(serializers.Serializer):
    a = serializers.CharField(required=True, help_text='A field description')
    b = serializers.CharField(required=False)
    read_only = serializers.CharField(read_only=True)
    hidden = serializers.HiddenField(default='hello')


class AnotherSerializer(serializers.Serializer):
    c = serializers.CharField(required=True)
    d = serializers.CharField(required=False)


class ExampleViewSet(ModelViewSet):
    pagination_class = ExamplePagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    serializer_class = ExampleSerializer

    @detail_route(methods=['put', 'post'], serializer_class=AnotherSerializer)
    def custom_action(self, request, pk):
        pass

    @list_route()
    def custom_list_action(self, request):
        pass

    def get_serializer(self, *args, **kwargs):
        assert self.request
        assert self.action
        return super(ExampleViewSet, self).get_serializer(*args, **kwargs)


class ExampleViewSet1(GenericViewSet):
    serializer_class = ExampleSerializer

    @detail_route(methods=['post'])
    def custom_action(self, request, pk):
        pass


class ExampleViewSet2(GenericViewSet):
    serializer_class = ExampleSerializer

    @detail_route(methods=['post'])
    def custom_action(self, request, pk):
        pass


class ExampleView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request, *args, **kwargs):
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

router = DefaultRouter(schema_title='Example API' if coreapi else None)
router.register('example1', ExampleViewSet1, base_name='example')
router.register('example2', ExampleViewSet2, base_name='example')
urlpatterns3 = [
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
                    'custom_list_action': coreapi.Link(
                        url='/example/custom_list_action/',
                        action='get'
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
            content={'example': MockCoreapiObject()}
        )
        self.assertEqual(response.data, expected)

    def test_links(self):
        client = APIClient()
        client.force_authenticate(MockUser())
        response = client.get('/', HTTP_ACCEPT='application/vnd.coreapi+json')
        self.assertEqual(response.status_code, 200)
        expected_links = [
            coreapi.Link(  # list
                url='/example/',
                action='get',
                fields=[
                    coreapi.Field('page', required=False, location='query'),
                    coreapi.Field('ordering', required=False, location='query')
                ]
            ),
            coreapi.Link(  # create
                url='/example/',
                action='post',
                encoding='application/json',
                fields=[
                    coreapi.Field('a', required=True, location='form', description='A field description'),
                    coreapi.Field('b', required=False, location='form')
                ]
            ),
            coreapi.Link(  # retrieve
                url='/example/{pk}/',
                action='get',
                fields=[
                    coreapi.Field('pk', required=True, location='path')
                ]
            ),
            coreapi.Link(  # custom_action post
                url='/example/{pk}/custom_action/',
                action='post',
                encoding='application/json',
                fields=[
                    coreapi.Field('pk', required=True, location='path'),
                    coreapi.Field('c', required=True, location='form'),
                    coreapi.Field('d', required=False, location='form'),
                ]
            ),
            coreapi.Link(  # custom_action put
                url='/example/{pk}/custom_action/',
                action='put',
                encoding='application/json',
                fields=[
                    coreapi.Field('pk', required=True, location='path'),
                    coreapi.Field('c', required=True, location='form'),
                    coreapi.Field('d', required=False, location='form'),
                ]
            ),
            coreapi.Link(  # custom_list_action
                url='/example/custom_list_action/',
                action='get'
            ),
            coreapi.Link(  # update
                url='/example/{pk}/',
                action='put',
                encoding='application/json',
                fields=[
                    coreapi.Field('pk', required=True, location='path'),
                    coreapi.Field('a', required=True, location='form', description='A field description'),
                    coreapi.Field('b', required=False, location='form')
                ]
            ),
            coreapi.Link(  # partial_update
                url='/example/{pk}/',
                action='patch',
                encoding='application/json',
                fields=[
                    coreapi.Field('pk', required=True, location='path'),
                    coreapi.Field('a', required=False, location='form', description='A field description'),
                    coreapi.Field('b', required=False, location='form')
                ]
            ),
            coreapi.Link(  # destroy
                url='/example/{pk}/',
                action='delete',
                fields=[
                    coreapi.Field('pk', required=True, location='path')
                ]
            ),
        ]

        response_links = response.data['example'].links.values()
        for link in expected_links:
            self.assertIn(link, response_links)


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaGenerator(TestCase):
    def test_similar_actions(self):
        schema_generator = SchemaGenerator(title='Test View', patterns=urlpatterns3)
        schema = schema_generator.get_schema()
        self.assertIn('example1', schema)
        self.assertIn('example2', schema)
        custom_action_1 = coreapi.Link(
            url='/example1/{pk}/custom_action/',
            action='post',
            encoding='application/json',
            fields=[
                coreapi.Field('pk', required=True, location='path'),
                coreapi.Field('a', required=True, location='form', description='A field description'),
                coreapi.Field('b', required=False, location='form')
            ]
        )
        custom_action_2 = coreapi.Link(
            url='/example2/{pk}/custom_action/',
            action='post',
            encoding='application/json',
            fields=[
                coreapi.Field('pk', required=True, location='path'),
                coreapi.Field('a', required=True, location='form', description='A field description'),
                coreapi.Field('b', required=False, location='form')
            ]
        )
        self.assertIn(custom_action_1, schema['example1'].links.values())
        self.assertIn(custom_action_2, schema['example2'].links.values())

    def test_view(self):
        schema_generator = SchemaGenerator(title='Test View', patterns=urlpatterns2)
        schema = schema_generator.get_schema()
        expected = coreapi.Document(
            url='',
            title='Test View',
            content={
                'example-view': {
                    'create': coreapi.Link(
                        url='/example-view/',
                        action='post',
                        fields=[]
                    ),
                    'read': coreapi.Link(
                        url='/example-view/',
                        action='get',
                        fields=[]
                    )
                }
            }
        )
        self.assertEquals(schema, expected)
