import unittest

import pytest
from django.conf.urls import include, url
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import TestCase, override_settings

from rest_framework import (
    filters, generics, pagination, permissions, serializers
)
from rest_framework.compat import coreapi, coreschema, get_regex_pattern, path
from rest_framework.decorators import action, api_view, schema
from rest_framework.request import Request
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework.schemas import (
    AutoSchema, ManualSchema, SchemaGenerator, get_schema_view
)
from rest_framework.schemas.generators import EndpointEnumerator
from rest_framework.schemas.inspectors import field_to_schema
from rest_framework.schemas.utils import is_list_view
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.utils import formatting
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .models import BasicModel, ForeignKeySource, ManyToManySource

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


class AnotherSerializerWithDictField(serializers.Serializer):
    a = serializers.DictField()


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

    @action(methods=['post'], detail=True, serializer_class=AnotherSerializer)
    def custom_action(self, request, pk):
        """
        A description of custom action.
        """
        raise NotImplementedError

    @action(methods=['post'], detail=True, serializer_class=AnotherSerializerWithDictField)
    def custom_action_with_dict_field(self, request, pk):
        """
        A custom action using a dict field in the serializer.
        """
        raise NotImplementedError

    @action(methods=['post'], detail=True, serializer_class=AnotherSerializerWithListFields)
    def custom_action_with_list_fields(self, request, pk):
        """
        A custom action using both list field and list serializer in the serializer.
        """
        raise NotImplementedError

    @action(detail=False)
    def custom_list_action(self, request):
        raise NotImplementedError

    @action(methods=['post', 'get'], detail=False, serializer_class=EmptySerializer)
    def custom_list_action_multiple_methods(self, request):
        """Custom description."""
        raise NotImplementedError

    @custom_list_action_multiple_methods.mapping.delete
    def custom_list_action_multiple_methods_delete(self, request):
        """Deletion description."""
        raise NotImplementedError

    @action(detail=False, schema=None)
    def excluded_action(self, request):
        pass

    def get_serializer(self, *args, **kwargs):
        assert self.request
        assert self.action
        return super(ExampleViewSet, self).get_serializer(*args, **kwargs)

    @action(methods=['get', 'post'], detail=False)
    def documented_custom_action(self, request):
        """
        get:
        A description of the get method on the custom action.

        post:
        A description of the post method on the custom action.
        """
        pass

    @documented_custom_action.mapping.put
    def put_documented_custom_action(self, request, *args, **kwargs):
        """
        A description of the put method on the custom action from mapping.
        """
        pass


if coreapi:
    schema_view = get_schema_view(title='Example API')
else:
    def schema_view(request):
        pass

router = DefaultRouter()
router.register('example', ExampleViewSet, basename='example')
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
                            action='get',
                            description='Custom description.',
                        )
                    },
                    'documented_custom_action': {
                        'read': coreapi.Link(
                            url='/example/documented_custom_action/',
                            action='get',
                            description='A description of the get method on the custom action.',
                        )
                    },
                    'read': coreapi.Link(
                        url='/example/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
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
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
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
                    'custom_action_with_dict_field': coreapi.Link(
                        url='/example/{id}/custom_action_with_dict_field/',
                        action='post',
                        encoding='application/json',
                        description='A custom action using a dict field in the serializer.',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('a', required=True, location='form', schema=coreschema.Object(title='A')),
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
                            action='get',
                            description='Custom description.',
                        ),
                        'create': coreapi.Link(
                            url='/example/custom_list_action_multiple_methods/',
                            action='post',
                            description='Custom description.',
                        ),
                        'delete': coreapi.Link(
                            url='/example/custom_list_action_multiple_methods/',
                            action='delete',
                            description='Deletion description.',
                        ),
                    },
                    'documented_custom_action': {
                        'read': coreapi.Link(
                            url='/example/documented_custom_action/',
                            action='get',
                            description='A description of the get method on the custom action.',
                        ),
                        'create': coreapi.Link(
                            url='/example/documented_custom_action/',
                            action='post',
                            description='A description of the post method on the custom action.',
                            encoding='application/json',
                            fields=[
                                coreapi.Field('a', required=True, location='form', schema=coreschema.String(title='A', description='A field description')),
                                coreapi.Field('b', required=False, location='form', schema=coreschema.String(title='B'))
                            ]
                        ),
                        'update': coreapi.Link(
                            url='/example/documented_custom_action/',
                            action='put',
                            description='A description of the put method on the custom action from mapping.',
                            encoding='application/json',
                            fields=[
                                coreapi.Field('a', required=True, location='form', schema=coreschema.String(title='A', description='A field description')),
                                coreapi.Field('b', required=False, location='form', schema=coreschema.String(title='B'))
                            ]
                        ),
                    },
                    'update': coreapi.Link(
                        url='/example/{id}/',
                        action='put',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('a', required=True, location='form', schema=coreschema.String(title='A', description=('A field description'))),
                            coreapi.Field('b', required=False, location='form', schema=coreschema.String(title='B')),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
                        ]
                    ),
                    'partial_update': coreapi.Link(
                        url='/example/{id}/',
                        action='patch',
                        encoding='application/json',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('a', required=False, location='form', schema=coreschema.String(title='A', description='A field description')),
                            coreapi.Field('b', required=False, location='form', schema=coreschema.String(title='B')),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
                        ]
                    ),
                    'delete': coreapi.Link(
                        url='/example/{id}/',
                        action='delete',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
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
            url(r'^example/?$', ExampleListView.as_view()),
            url(r'^example/(?P<pk>\d+)/?$', ExampleDetailView.as_view()),
            url(r'^example/(?P<pk>\d+)/sub/?$', ExampleDetailView.as_view()),
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
@unittest.skipUnless(path, 'needs Django 2')
class TestSchemaGeneratorDjango2(TestCase):
    def setUp(self):
        self.patterns = [
            path('example/', ExampleListView.as_view()),
            path('example/<int:pk>/', ExampleDetailView.as_view()),
            path('example/<int:pk>/sub/', ExampleDetailView.as_view()),
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
            url(r'^api/v1/example/?$', ExampleListView.as_view()),
            url(r'^api/v1/example/(?P<pk>\d+)/?$', ExampleDetailView.as_view()),
            url(r'^api/v1/example/(?P<pk>\d+)/sub/?$', ExampleDetailView.as_view()),
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
        router.register('example1', MethodLimitedViewSet, basename='example1')
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
                            action='get',
                            description='Custom description.',
                        )
                    },
                    'documented_custom_action': {
                        'read': coreapi.Link(
                            url='/example1/documented_custom_action/',
                            action='get',
                            description='A description of the get method on the custom action.',
                        ),
                    },
                    'read': coreapi.Link(
                        url='/example1/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String()),
                            coreapi.Field('ordering', required=False, location='query', schema=coreschema.String(title='Ordering', description='Which field to use when ordering the results.'))
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
        router.register('example1', Http404ExampleViewSet, basename='example1')
        router.register('example2', PermissionDeniedExampleViewSet, basename='example2')
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


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = ('id', 'name', 'target')


class ForeignKeySourceView(generics.CreateAPIView):
    queryset = ForeignKeySource.objects.all()
    serializer_class = ForeignKeySourceSerializer


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaGeneratorWithForeignKey(TestCase):
    def setUp(self):
        self.patterns = [
            url(r'^example/?$', ForeignKeySourceView.as_view()),
        ]

    def test_schema_for_regular_views(self):
        """
        Ensure that AutoField foreign keys are output as Integer.
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
                        encoding='application/json',
                        fields=[
                            coreapi.Field('name', required=True, location='form', schema=coreschema.String(title='Name')),
                            coreapi.Field('target', required=True, location='form', schema=coreschema.Integer(description='Target', title='Target')),
                        ]
                    )
                }
            }
        )
        assert schema == expected


class ManyToManySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManySource
        fields = ('id', 'name', 'targets')


class ManyToManySourceView(generics.CreateAPIView):
    queryset = ManyToManySource.objects.all()
    serializer_class = ManyToManySourceSerializer


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class TestSchemaGeneratorWithManyToMany(TestCase):
    def setUp(self):
        self.patterns = [
            url(r'^example/?$', ManyToManySourceView.as_view()),
        ]

    def test_schema_for_regular_views(self):
        """
        Ensure that AutoField many to many fields are output as Integer.
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
                        encoding='application/json',
                        fields=[
                            coreapi.Field('name', required=True, location='form', schema=coreschema.String(title='Name')),
                            coreapi.Field('targets', required=True, location='form', schema=coreschema.Array(title='Targets', items=coreschema.Integer())),
                        ]
                    )
                }
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


class CustomViewInspector(AutoSchema):
    """A dummy AutoSchema subclass"""
    pass


class TestAutoSchema(TestCase):

    def test_apiview_schema_descriptor(self):
        view = APIView()
        assert hasattr(view, 'schema')
        assert isinstance(view.schema, AutoSchema)

    def test_set_custom_inspector_class_on_view(self):
        class CustomView(APIView):
            schema = CustomViewInspector()

        view = CustomView()
        assert isinstance(view.schema, CustomViewInspector)

    def test_set_custom_inspector_class_via_settings(self):
        with override_settings(REST_FRAMEWORK={'DEFAULT_SCHEMA_CLASS': 'tests.test_schemas.CustomViewInspector'}):
            view = APIView()
            assert isinstance(view.schema, CustomViewInspector)

    def test_get_link_requires_instance(self):
        descriptor = APIView.schema  # Accessed from class
        with pytest.raises(AssertionError):
            descriptor.get_link(None, None, None)  # ???: Do the dummy arguments require a tighter assert?

    @pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
    def test_update_fields(self):
        """
        That updating fields by-name helper is correct

        Recall: `update_fields(fields, update_with)`
        """
        schema = AutoSchema()
        fields = []

        # Adds a field...
        fields = schema.update_fields(fields, [
            coreapi.Field(
                "my_field",
                required=True,
                location="path",
                schema=coreschema.String()
            ),
        ])

        assert len(fields) == 1
        assert fields[0].name == "my_field"

        # Replaces a field...
        fields = schema.update_fields(fields, [
            coreapi.Field(
                "my_field",
                required=False,
                location="path",
                schema=coreschema.String()
            ),
        ])

        assert len(fields) == 1
        assert fields[0].required is False

    @pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
    def test_get_manual_fields(self):
        """That get_manual_fields is applied during get_link"""

        class CustomView(APIView):
            schema = AutoSchema(manual_fields=[
                coreapi.Field(
                    "my_extra_field",
                    required=True,
                    location="path",
                    schema=coreschema.String()
                ),
            ])

        view = CustomView()
        link = view.schema.get_link('/a/url/{id}/', 'GET', '')
        fields = link.fields

        assert len(fields) == 2
        assert "my_extra_field" in [f.name for f in fields]

    @pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
    def test_viewset_action_with_schema(self):
        class CustomViewSet(GenericViewSet):
            @action(detail=True, schema=AutoSchema(manual_fields=[
                coreapi.Field(
                    "my_extra_field",
                    required=True,
                    location="path",
                    schema=coreschema.String()
                ),
            ]))
            def extra_action(self, pk, **kwargs):
                pass

        router = SimpleRouter()
        router.register(r'detail', CustomViewSet, basename='detail')

        generator = SchemaGenerator()
        view = generator.create_view(router.urls[0].callback, 'GET')
        link = view.schema.get_link('/a/url/{id}/', 'GET', '')
        fields = link.fields

        assert len(fields) == 2
        assert "my_extra_field" in [f.name for f in fields]

    @pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
    def test_viewset_action_with_null_schema(self):
        class CustomViewSet(GenericViewSet):
            @action(detail=True, schema=None)
            def extra_action(self, pk, **kwargs):
                pass

        router = SimpleRouter()
        router.register(r'detail', CustomViewSet, basename='detail')

        generator = SchemaGenerator()
        view = generator.create_view(router.urls[0].callback, 'GET')
        assert view.schema is None

    @pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
    def test_view_with_manual_schema(self):

        path = '/example'
        method = 'get'
        base_url = None

        fields = [
            coreapi.Field(
                "first_field",
                required=True,
                location="path",
                schema=coreschema.String()
            ),
            coreapi.Field(
                "second_field",
                required=True,
                location="path",
                schema=coreschema.String()
            ),
            coreapi.Field(
                "third_field",
                required=True,
                location="path",
                schema=coreschema.String()
            ),
        ]
        description = "A test endpoint"

        class CustomView(APIView):
            """
            ManualSchema takes list of fields for endpoint.
            - Provides url and action, which are always dynamic
            """
            schema = ManualSchema(fields, description)

        expected = coreapi.Link(
            url=path,
            action=method,
            fields=fields,
            description=description
        )

        view = CustomView()
        link = view.schema.get_link(path, method, base_url)
        assert link == expected

    @unittest.skipUnless(coreschema, 'coreschema is not installed')
    def test_field_to_schema(self):
        label = 'Test label'
        help_text = 'This is a helpful test text'

        cases = [
            # tuples are ([field], [expected schema])
            # TODO: Add remaining cases
            (
                serializers.BooleanField(label=label, help_text=help_text),
                coreschema.Boolean(title=label, description=help_text)
            ),
            (
                serializers.DecimalField(1000, 1000, label=label, help_text=help_text),
                coreschema.Number(title=label, description=help_text)
            ),
            (
                serializers.FloatField(label=label, help_text=help_text),
                coreschema.Number(title=label, description=help_text)
            ),
            (
                serializers.IntegerField(label=label, help_text=help_text),
                coreschema.Integer(title=label, description=help_text)
            ),
            (
                serializers.DateField(label=label, help_text=help_text),
                coreschema.String(title=label, description=help_text, format='date')
            ),
            (
                serializers.DateTimeField(label=label, help_text=help_text),
                coreschema.String(title=label, description=help_text, format='date-time')
            ),
            (
                serializers.JSONField(label=label, help_text=help_text),
                coreschema.Object(title=label, description=help_text)
            ),
        ]

        for case in cases:
            self.assertEqual(field_to_schema(case[0]), case[1])


def test_docstring_is_not_stripped_by_get_description():
    class ExampleDocstringAPIView(APIView):
        """
        === title

         * item a
           * item a-a
           * item a-b
         * item b

         - item 1
         - item 2

            code block begin
            code
            code
            code
            code block end

        the end
        """

        def get(self, *args, **kwargs):
            pass

        def post(self, request, *args, **kwargs):
            pass

    view = ExampleDocstringAPIView()
    schema = view.schema
    descr = schema.get_description('example', 'get')
    # the first and last character are '\n' correctly removed by get_description
    assert descr == formatting.dedent(ExampleDocstringAPIView.__doc__[1:][:-1])


# Views for SchemaGenerationExclusionTests
class ExcludedAPIView(APIView):
    schema = None

    def get(self, request, *args, **kwargs):
        pass


@api_view(['GET'])
@schema(None)
def excluded_fbv(request):
    pass


@api_view(['GET'])
def included_fbv(request):
    pass


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class SchemaGenerationExclusionTests(TestCase):
    def setUp(self):
        self.patterns = [
            url('^excluded-cbv/$', ExcludedAPIView.as_view()),
            url('^excluded-fbv/$', excluded_fbv),
            url('^included-fbv/$', included_fbv),
        ]

    def test_schema_generator_excludes_correctly(self):
        """Schema should not include excluded views"""
        generator = SchemaGenerator(title='Exclusions', patterns=self.patterns)
        schema = generator.get_schema()
        expected = coreapi.Document(
            url='',
            title='Exclusions',
            content={
                'included-fbv': {
                    'list': coreapi.Link(url='/included-fbv/', action='get')
                }
            }
        )

        assert len(schema.data) == 1
        assert 'included-fbv' in schema.data
        assert schema == expected

    def test_endpoint_enumerator_excludes_correctly(self):
        """It is responsibility of EndpointEnumerator to exclude views"""
        inspector = EndpointEnumerator(self.patterns)
        endpoints = inspector.get_api_endpoints()

        assert len(endpoints) == 1
        path, method, callback = endpoints[0]
        assert path == '/included-fbv/'

    def test_should_include_endpoint_excludes_correctly(self):
        """This is the specific method that should handle the exclusion"""
        inspector = EndpointEnumerator(self.patterns)

        # Not pretty. Mimics internals of EndpointEnumerator to put should_include_endpoint under test
        pairs = [(inspector.get_path_from_regex(get_regex_pattern(pattern)), pattern.callback)
                 for pattern in self.patterns]

        should_include = [
            inspector.should_include_endpoint(*pair) for pair in pairs
        ]

        expected = [False, False, True]

        assert should_include == expected


@api_view(["GET"])
def simple_fbv(request):
    pass


class BasicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = "__all__"


class NamingCollisionView(generics.RetrieveUpdateDestroyAPIView):
    queryset = BasicModel.objects.all()
    serializer_class = BasicModelSerializer


class BasicNamingCollisionView(generics.RetrieveAPIView):
    queryset = BasicModel.objects.all()


class NamingCollisionViewSet(GenericViewSet):
    """
    Example via: https://stackoverflow.com/questions/43778668/django-rest-framwork-occured-typeerror-link-object-does-not-support-item-ass/
    """
    permision_class = ()

    @action(detail=False)
    def detail(self, request):
        return {}

    @action(detail=False, url_path='detail/export')
    def detail_export(self, request):
        return {}


naming_collisions_router = SimpleRouter()
naming_collisions_router.register(r'collision', NamingCollisionViewSet, basename="collision")


@pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
class TestURLNamingCollisions(TestCase):
    """
    Ref: https://github.com/encode/django-rest-framework/issues/4704
    """
    def test_manually_routing_nested_routes(self):
        patterns = [
            url(r'^test', simple_fbv),
            url(r'^test/list/', simple_fbv),
        ]

        generator = SchemaGenerator(title='Naming Colisions', patterns=patterns)
        schema = generator.get_schema()

        expected = coreapi.Document(
            url='',
            title='Naming Colisions',
            content={
                'test': {
                    'list': {
                        'list': coreapi.Link(url='/test/list/', action='get')
                    },
                    'list_0': coreapi.Link(url='/test', action='get')
                }
            }
        )

        assert expected == schema

    def _verify_cbv_links(self, loc, url, methods=None, suffixes=None):
        if methods is None:
            methods = ('read', 'update', 'partial_update', 'delete')
        if suffixes is None:
            suffixes = (None for m in methods)

        for method, suffix in zip(methods, suffixes):
            if suffix is not None:
                key = '{}_{}'.format(method, suffix)
            else:
                key = method
            assert loc[key].url == url

    def test_manually_routing_generic_view(self):
        patterns = [
            url(r'^test', NamingCollisionView.as_view()),
            url(r'^test/retrieve/', NamingCollisionView.as_view()),
            url(r'^test/update/', NamingCollisionView.as_view()),

            # Fails with method names:
            url(r'^test/get/', NamingCollisionView.as_view()),
            url(r'^test/put/', NamingCollisionView.as_view()),
            url(r'^test/delete/', NamingCollisionView.as_view()),
        ]

        generator = SchemaGenerator(title='Naming Colisions', patterns=patterns)

        schema = generator.get_schema()

        self._verify_cbv_links(schema['test']['delete'], '/test/delete/')
        self._verify_cbv_links(schema['test']['put'], '/test/put/')
        self._verify_cbv_links(schema['test']['get'], '/test/get/')
        self._verify_cbv_links(schema['test']['update'], '/test/update/')
        self._verify_cbv_links(schema['test']['retrieve'], '/test/retrieve/')
        self._verify_cbv_links(schema['test'], '/test', suffixes=(None, '0', None, '0'))

    def test_from_router(self):
        patterns = [
            url(r'from-router', include(naming_collisions_router.urls)),
        ]

        generator = SchemaGenerator(title='Naming Colisions', patterns=patterns)
        schema = generator.get_schema()

        # not important here
        desc_0 = schema['detail']['detail_export'].description
        desc_1 = schema['detail_0'].description

        expected = coreapi.Document(
            url='',
            title='Naming Colisions',
            content={
                'detail': {
                    'detail_export': coreapi.Link(
                        url='/from-routercollision/detail/export/',
                        action='get',
                        description=desc_0)
                },
                'detail_0': coreapi.Link(
                    url='/from-routercollision/detail/',
                    action='get',
                    description=desc_1
                )
            }
        )

        assert schema == expected

    def test_url_under_same_key_not_replaced(self):
        patterns = [
            url(r'example/(?P<pk>\d+)/$', BasicNamingCollisionView.as_view()),
            url(r'example/(?P<slug>\w+)/$', BasicNamingCollisionView.as_view()),
        ]

        generator = SchemaGenerator(title='Naming Colisions', patterns=patterns)
        schema = generator.get_schema()

        assert schema['example']['read'].url == '/example/{id}/'
        assert schema['example']['read_0'].url == '/example/{slug}/'

    def test_url_under_same_key_not_replaced_another(self):

        patterns = [
            url(r'^test/list/', simple_fbv),
            url(r'^test/(?P<pk>\d+)/list/', simple_fbv),
        ]

        generator = SchemaGenerator(title='Naming Colisions', patterns=patterns)
        schema = generator.get_schema()

        assert schema['test']['list']['list'].url == '/test/list/'
        assert schema['test']['list']['list_0'].url == '/test/{id}/list/'


def test_is_list_view_recognises_retrieve_view_subclasses():
    class TestView(generics.RetrieveAPIView):
        pass

    path = '/looks/like/a/list/view/'
    method = 'get'
    view = TestView()

    is_list = is_list_view(path, method, view)
    assert not is_list, "RetrieveAPIView subclasses should not be classified as list views."


def test_head_and_options_methods_are_excluded():
    """
    Regression test for #5528
    https://github.com/encode/django-rest-framework/issues/5528

    Viewset OPTIONS actions were not being correctly excluded

    Initial cases here shown to be working as expected.
    """

    @api_view(['options', 'get'])
    def fbv(request):
        pass

    inspector = EndpointEnumerator()

    path = '/a/path/'
    callback = fbv

    assert inspector.should_include_endpoint(path, callback)
    assert inspector.get_allowed_methods(callback) == ["GET"]

    class AnAPIView(APIView):

        def get(self, request, *args, **kwargs):
            pass

        def options(self, request, *args, **kwargs):
            pass

    callback = AnAPIView.as_view()

    assert inspector.should_include_endpoint(path, callback)
    assert inspector.get_allowed_methods(callback) == ["GET"]

    class AViewSet(ModelViewSet):

        @action(methods=['options', 'get'], detail=True)
        def custom_action(self, request, pk):
            pass

    callback = AViewSet.as_view({
        "options": "custom_action",
        "get": "custom_action"
    })

    assert inspector.should_include_endpoint(path, callback)
    assert inspector.get_allowed_methods(callback) == ["GET"]


@pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
class TestAutoSchemaAllowsFilters(object):
    class MockAPIView(APIView):
        filter_backends = [filters.OrderingFilter]

    def _test(self, method):
        view = self.MockAPIView()
        fields = view.schema.get_filter_fields('', method)
        field_names = [f.name for f in fields]

        return 'ordering' in field_names

    def test_get(self):
        assert self._test('get')

    def test_GET(self):
        assert self._test('GET')

    def test_put(self):
        assert self._test('put')

    def test_PUT(self):
        assert self._test('PUT')

    def test_patch(self):
        assert self._test('patch')

    def test_PATCH(self):
        assert self._test('PATCH')

    def test_delete(self):
        assert self._test('delete')

    def test_DELETE(self):
        assert self._test('DELETE')

    def test_post(self):
        assert not self._test('post')

    def test_POST(self):
        assert not self._test('POST')

    def test_foo(self):
        assert not self._test('foo')

    def test_FOO(self):
        assert not self._test('FOO')


@pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
def test_schema_handles_exception():
    schema_view = get_schema_view(permission_classes=[DenyAllUsingPermissionDenied])
    request = factory.get('/')
    response = schema_view(request)
    response.render()
    assert response.status_code == 403
    assert "You do not have permission to perform this action." in str(response.content)
