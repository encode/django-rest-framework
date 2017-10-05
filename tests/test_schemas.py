import unittest

import pytest
from django.conf.urls import include, url
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import TestCase, override_settings

from rest_framework import (
    filters, generics, pagination, permissions, serializers
)
from rest_framework.compat import coreapi, coreschema
from rest_framework.decorators import (
    api_view, detail_route, list_route, schema
)
from rest_framework.request import Request
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework.schemas import (
    AutoSchema, ManualSchema, SchemaGenerator, get_schema_view
)
from rest_framework.schemas.generators import EndpointEnumerator
from rest_framework.schemas.utils import is_list_view
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.utils import formatting
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from .models import BasicModel

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


class TestDescriptor(TestCase):

    def test_apiview_schema_descriptor(self):
        view = APIView()
        assert hasattr(view, 'schema')
        assert isinstance(view.schema, AutoSchema)

    def test_get_link_requires_instance(self):
        descriptor = APIView.schema  # Accessed from class
        with pytest.raises(AssertionError):
            descriptor.get_link(None, None, None)  # ???: Do the dummy arguments require a tighter assert?

    def test_manual_fields(self):

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
        pairs = [(inspector.get_path_from_regex(pattern.regex.pattern), pattern.callback)
                 for pattern in self.patterns]

        should_include = [
            inspector.should_include_endpoint(*pair) for pair in pairs
        ]

        expected = [False, False, True]

        assert should_include == expected

    def test_deprecations(self):
        with pytest.warns(PendingDeprecationWarning) as record:
            @api_view(["GET"], exclude_from_schema=True)
            def view(request):
                pass

        assert len(record) == 1
        assert str(record[0].message) == (
            "The `exclude_from_schema` argument to `api_view` is pending "
            "deprecation. Use the `schema` decorator instead, passing `None`."
        )

        class OldFashionedExcludedView(APIView):
            exclude_from_schema = True

            def get(self, request, *args, **kwargs):
                pass

        patterns = [
            url('^excluded-old-fashioned/$', OldFashionedExcludedView.as_view()),
        ]

        inspector = EndpointEnumerator(patterns)
        with pytest.warns(PendingDeprecationWarning) as record:
            inspector.get_api_endpoints()

        assert len(record) == 1
        assert str(record[0].message) == (
            "The `OldFashionedExcludedView.exclude_from_schema` attribute is "
            "pending deprecation. Set `schema = None` instead."
        )


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


class NamingCollisionViewSet(GenericViewSet):
    """
    Example via: https://stackoverflow.com/questions/43778668/django-rest-framwork-occured-typeerror-link-object-does-not-support-item-ass/
    """
    permision_class = ()

    @list_route()
    def detail(self, request):
        return {}

    @list_route(url_path='detail/export')
    def detail_export(self, request):
        return {}


naming_collisions_router = SimpleRouter()
naming_collisions_router.register(r'collision', NamingCollisionViewSet, base_name="collision")


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

        with pytest.raises(ValueError):
            generator.get_schema()

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

        with pytest.raises(ValueError):
            generator.get_schema()

    def test_from_router(self):
        patterns = [
            url(r'from-router', include(naming_collisions_router.urls)),
        ]

        generator = SchemaGenerator(title='Naming Colisions', patterns=patterns)

        with pytest.raises(ValueError):
            generator.get_schema()


def test_is_list_view_recognises_retrieve_view_subclasses():
    class TestView(generics.RetrieveAPIView):
        pass

    path = '/looks/like/a/list/view/'
    method = 'get'
    view = TestView()

    is_list = is_list_view(path, method, view)
    assert not is_list, "RetrieveAPIView subclasses should not be classified as list views."
