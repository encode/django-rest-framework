import unittest

from django.conf.urls import include, url
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import TestCase, override_settings

from rest_framework import filters, pagination, permissions, serializers
from rest_framework.compat import coreapi, coreschema
from rest_framework.decorators import detail_route, list_route
from rest_framework.request import Request
from rest_framework.routers import DefaultRouter
from rest_framework.schemas import SchemaGenerator, get_schema_view
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

factory = APIRequestFactory()


class MockUser(object):
    def is_authenticated(self):
        return True


class ExamplePagination(pagination.PageNumberPagination):
    page_size = 100
    page_size_query_param = 'page_size'


class EmptySerializer(serializers.Serializer):
    pass


class ExampleSerializer(serializers.Serializer):
    a = serializers.CharField(required=True, help_text='A field description')
    b = serializers.CharField(required=False)
    read_only = serializers.CharField(read_only=True)
    hidden = serializers.HiddenField(default='hello')


class AnotherSerializerWithListFields(serializers.Serializer):
    a = serializers.ListField(child=serializers.IntegerField())
    b = serializers.ListSerializer(child=serializers.CharField())


class AnotherSerializer(serializers.Serializer):
    c = serializers.CharField(required=True)
    d = serializers.CharField(required=False)


class ExampleViewSet(ModelViewSet):
    pagination_class = ExamplePagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    serializer_class = ExampleSerializer

    @detail_route(methods=['post'], serializer_class=AnotherSerializer)
    def custom_action(self, request, pk):
        """
        A description of custom action.
        """
        return super(ExampleSerializer, self).retrieve(self, request)

    @detail_route(methods=['post'], serializer_class=AnotherSerializerWithListFields)
    def custom_action_with_list_fields(self, request, pk):
        """
        A custom action using both list field and list serializer in the serializer.
        """
        return super(ExampleSerializer, self).retrieve(self, request)

    @list_route()
    def custom_list_action(self, request):
        return super(ExampleViewSet, self).list(self, request)

    @list_route(methods=['post', 'get'], serializer_class=EmptySerializer)
    def custom_list_action_multiple_methods(self, request):
        return super(ExampleViewSet, self).list(self, request)

    def get_serializer(self, *args, **kwargs):
        assert self.request
        assert self.action
        return super(ExampleViewSet, self).get_serializer(*args, **kwargs)


if coreapi:
    schema_view = get_schema_view(title='Example API')
else:
    def schema_view(request):
        pass

router = DefaultRouter()
router.register('example', ExampleViewSet, base_name='example')
urlpatterns = [
    url(r'^$', schema_view),
    url(r'^', include(router.urls))
]


@unittest.skipUnless(coreapi, 'coreapi is not installed')
@override_settings(ROOT_URLCONF='tests.test_schemas')
class TestRouterGeneratedSchema(TestCase):
    def test_anonymous_request(self):
        client = APIClient()
        response = client.get('/', HTTP_ACCEPT='application/coreapi+json')
        assert response.status_code == 200
        expected = coreapi.Document(
            url='http://testserver/',
            title='Example API',
            content={
                'example': {
                    'list': coreapi.Link(
                        url='/example/',
                        action='get',
                        fields=[
                            coreapi.Field('page', required=False, location='query', schema=coreschema.Integer(title='Page', description='A page number within the paginated result set.')),
                            coreapi.Field('page_size', required=False, location='query', schema=coreschema.Integer(title='Page size', description='Number of results to return per page.')),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
                        ]
                    ),
                    'custom_list_action': coreapi.Link(
                        url='/example/custom_list_action/',
                        action='get'
                    ),
                    'custom_list_action_multiple_methods': {
                        'read': coreapi.Link(
                            url='/example/custom_list_action_multiple_methods/',
                            action='get'
                        )
                    },
                    'read': coreapi.Link(
                        url='/example/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
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
                'example': {
                    'list': coreapi.Link(
                        url='/example/',
                        action='get',
                        fields=[
                            coreapi.Field('page', required=False, location='query', schema=coreschema.Integer(title='Page', description='A page number within the paginated result set.')),
                            coreapi.Field('page_size', required=False, location='query', schema=coreschema.Integer(title='Page size', description='Number of results to return per page.')),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
                        ]
                    ),
                    'create': coreapi.Link(
                        url='/example/',
                        action='post',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('a', required=True, location='form', schema=coreschema.String(title='A', description='A field description')),
                            coreapi.Field('b', required=False, location='form', schema=coreschema.String(title='B'))
                        ]
                    ),
                    'read': coreapi.Link(
                        url='/example/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    ),
                    'custom_action': coreapi.Link(
                        url='/example/{id}/custom_action/',
                        action='post',
                        encoding='application/json',
                        description='A description of custom action.',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('c', required=True, location='form', schema=coreschema.String(title='C')),
                            coreapi.Field('d', required=False, location='form', schema=coreschema.String(title='D')),
                        ]
                    ),
                    'custom_action_with_list_fields': coreapi.Link(
                        url='/example/{id}/custom_action_with_list_fields/',
                        action='post',
                        encoding='application/json',
                        description='A custom action using both list field and list serializer in the serializer.',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('a', required=True, location='form', schema=coreschema.Array(title='A', items=coreschema.Integer())),
                            coreapi.Field('b', required=True, location='form', schema=coreschema.Array(title='B', items=coreschema.String())),
                        ]
                    ),
                    'custom_list_action': coreapi.Link(
                        url='/example/custom_list_action/',
                        action='get'
                    ),
                    'custom_list_action_multiple_methods': {
                        'read': coreapi.Link(
                            url='/example/custom_list_action_multiple_methods/',
                            action='get'
                        ),
                        'create': coreapi.Link(
                            url='/example/custom_list_action_multiple_methods/',
                            action='post'
                        )
                    },
                    'update': coreapi.Link(
                        url='/example/{id}/',
                        action='put',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('a', required=True, location='form', schema=coreschema.String(title='A', description=('A field description'))),
                            coreapi.Field('b', required=False, location='form', schema=coreschema.String(title='B'))
                        ]
                    ),
                    'partial_update': coreapi.Link(
                        url='/example/{id}/',
                        action='patch',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('a', required=False, location='form', schema=coreschema.String(title='A', description='A field description')),
                            coreapi.Field('b', required=False, location='form', schema=coreschema.String(title='B'))
                        ]
                    ),
                    'delete': coreapi.Link(
                        url='/example/{id}/',
                        action='delete',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    )
                }
            }
        )
        assert response.data == expected


class DenyAllUsingHttp404(permissions.BasePermission):

    def has_permission(self, request, view):
        raise Http404()

    def has_object_permission(self, request, view, obj):
        raise Http404()


class DenyAllUsingPermissionDenied(permissions.BasePermission):

    def has_permission(self, request, view):
        raise PermissionDenied()

    def has_object_permission(self, request, view, obj):
        raise PermissionDenied()


class Http404ExampleViewSet(ExampleViewSet):
    permission_classes = [DenyAllUsingHttp404]


class PermissionDeniedExampleViewSet(ExampleViewSet):
    permission_classes = [DenyAllUsingPermissionDenied]


class MethodLimitedViewSet(ExampleViewSet):
    permission_classes = []
    http_method_names = ['get', 'head', 'options']


class ExampleListView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, *args, **kwargs):
        pass

    def post(self, request, *args, **kwargs):
        pass


class ExampleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, *args, **kwargs):
        pass


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaGenerator(TestCase):
    def setUp(self):
        self.patterns = [
            url('^example/?$', ExampleListView.as_view()),
            url('^example/(?P<pk>\d+)/?$', ExampleDetailView.as_view()),
            url('^example/(?P<pk>\d+)/sub/?$', ExampleDetailView.as_view()),
        ]

    def test_schema_for_regular_views(self):
        """
        Ensure that schema generation works for APIView classes.
        """
        generator = SchemaGenerator(title='Example API', patterns=self.patterns)
        schema = generator.get_schema()
        expected = coreapi.Document(
            url='',
            title='Example API',
            content={
                'example': {
                    'create': coreapi.Link(
                        url='/example/',
                        action='post',
                        fields=[]
                    ),
                    'list': coreapi.Link(
                        url='/example/',
                        action='get',
                        fields=[]
                    ),
                    'read': coreapi.Link(
                        url='/example/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    ),
                    'sub': {
                        'list': coreapi.Link(
                            url='/example/{id}/sub/',
                            action='get',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        )
                    }
                }
            }
        )
        assert schema == expected


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaGeneratorNotAtRoot(TestCase):
    def setUp(self):
        self.patterns = [
            url('^api/v1/example/?$', ExampleListView.as_view()),
            url('^api/v1/example/(?P<pk>\d+)/?$', ExampleDetailView.as_view()),
            url('^api/v1/example/(?P<pk>\d+)/sub/?$', ExampleDetailView.as_view()),
        ]

    def test_schema_for_regular_views(self):
        """
        Ensure that schema generation with an API that is not at the URL
        root continues to use correct structure for link keys.
        """
        generator = SchemaGenerator(title='Example API', patterns=self.patterns)
        schema = generator.get_schema()
        expected = coreapi.Document(
            url='',
            title='Example API',
            content={
                'example': {
                    'create': coreapi.Link(
                        url='/api/v1/example/',
                        action='post',
                        fields=[]
                    ),
                    'list': coreapi.Link(
                        url='/api/v1/example/',
                        action='get',
                        fields=[]
                    ),
                    'read': coreapi.Link(
                        url='/api/v1/example/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    ),
                    'sub': {
                        'list': coreapi.Link(
                            url='/api/v1/example/{id}/sub/',
                            action='get',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        )
                    }
                }
            }
        )
        assert schema == expected


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaGeneratorWithMethodLimitedViewSets(TestCase):
    def setUp(self):
        router = DefaultRouter()
        router.register('example1', MethodLimitedViewSet, base_name='example1')
        self.patterns = [
            url(r'^', include(router.urls))
        ]

    def test_schema_for_regular_views(self):
        """
        Ensure that schema generation works for ViewSet classes
        with method limitation by Django CBV's http_method_names attribute
        """
        generator = SchemaGenerator(title='Example API', patterns=self.patterns)
        request = factory.get('/example1/')
        schema = generator.get_schema(Request(request))

        expected = coreapi.Document(
            url='http://testserver/example1/',
            title='Example API',
            content={
                'example1': {
                    'list': coreapi.Link(
                        url='/example1/',
                        action='get',
                        fields=[
                            coreapi.Field('page', required=False, location='query', schema=coreschema.Integer(title='Page', description='A page number within the paginated result set.')),
                            coreapi.Field('page_size', required=False, location='query', schema=coreschema.Integer(title='Page size', description='Number of results to return per page.')),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
                        ]
                    ),
                    'custom_list_action': coreapi.Link(
                        url='/example1/custom_list_action/',
                        action='get'
                    ),
                    'custom_list_action_multiple_methods': {
                        'read': coreapi.Link(
                            url='/example1/custom_list_action_multiple_methods/',
                            action='get'
                        )
                    },
                    'read': coreapi.Link(
                        url='/example1/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    )
                }
            }
        )
        assert schema == expected


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaGeneratorWithRestrictedViewSets(TestCase):
    def setUp(self):
        router = DefaultRouter()
        router.register('example1', Http404ExampleViewSet, base_name='example1')
        router.register('example2', PermissionDeniedExampleViewSet, base_name='example2')
        self.patterns = [
            url('^example/?$', ExampleListView.as_view()),
            url(r'^', include(router.urls))
        ]

    def test_schema_for_regular_views(self):
        """
        Ensure that schema generation works for ViewSet classes
        with permission classes raising exceptions.
        """
        generator = SchemaGenerator(title='Example API', patterns=self.patterns)
        request = factory.get('/')
        schema = generator.get_schema(Request(request))
        expected = coreapi.Document(
            url='http://testserver/',
            title='Example API',
            content={
                'example': {
                    'list': coreapi.Link(
                        url='/example/',
                        action='get',
                        fields=[]
                    ),
                },
            }
        )
        assert schema == expected


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class Test4605Regression(TestCase):
    def test_4605_regression(self):
        generator = SchemaGenerator()
        prefix = generator.determine_path_prefix([
            '/api/v1/items/',
            '/auth/convert-token/'
        ])
        assert prefix == '/'
