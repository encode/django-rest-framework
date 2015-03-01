from __future__ import unicode_literals
from django.conf.urls import url, include
from django.db import models
from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers, viewsets, permissions
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter, DefaultRouter
from rest_framework.test import APIRequestFactory
from collections import namedtuple

factory = APIRequestFactory()


class RouterTestModel(models.Model):
    uuid = models.CharField(max_length=20)
    text = models.CharField(max_length=200)


class NoteSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='routertestmodel-detail', lookup_field='uuid')

    class Meta:
        model = RouterTestModel
        fields = ('url', 'uuid', 'text')


class NoteViewSet(viewsets.ModelViewSet):
    queryset = RouterTestModel.objects.all()
    serializer_class = NoteSerializer
    lookup_field = 'uuid'


class MockViewSet(viewsets.ModelViewSet):
    queryset = None
    serializer_class = None


notes_router = SimpleRouter()
notes_router.register(r'notes', NoteViewSet)

namespaced_router = DefaultRouter()
namespaced_router.register(r'example', MockViewSet, base_name='example')

urlpatterns = [
    url(r'^non-namespaced/', include(namespaced_router.urls)),
    url(r'^namespaced/', include(namespaced_router.urls, namespace='example')),
    url(r'^example/', include(notes_router.urls)),
]


class BasicViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'method': 'list'})

    @detail_route(methods=['post'])
    def action1(self, request, *args, **kwargs):
        return Response({'method': 'action1'})

    @detail_route(methods=['post'])
    def action2(self, request, *args, **kwargs):
        return Response({'method': 'action2'})

    @detail_route(methods=['post', 'delete'])
    def action3(self, request, *args, **kwargs):
        return Response({'method': 'action2'})

    @detail_route()
    def link1(self, request, *args, **kwargs):
        return Response({'method': 'link1'})

    @detail_route()
    def link2(self, request, *args, **kwargs):
        return Response({'method': 'link2'})


class TestSimpleRouter(TestCase):
    def setUp(self):
        self.router = SimpleRouter()

    def test_link_and_action_decorator(self):
        routes = self.router.get_routes(BasicViewSet)
        decorator_routes = routes[2:]
        # Make sure all these endpoints exist and none have been clobbered
        for i, endpoint in enumerate(['action1', 'action2', 'action3', 'link1', 'link2']):
            route = decorator_routes[i]
            # check url listing
            self.assertEqual(route.url,
                             '^{{prefix}}/{{lookup}}/{0}{{trailing_slash}}$'.format(endpoint))
            # check method to function mapping
            if endpoint == 'action3':
                methods_map = ['post', 'delete']
            elif endpoint.startswith('action'):
                methods_map = ['post']
            else:
                methods_map = ['get']
            for method in methods_map:
                self.assertEqual(route.mapping[method], endpoint)


class TestRootView(TestCase):
    urls = 'tests.test_routers'

    def test_retrieve_namespaced_root(self):
        response = self.client.get('/namespaced/')
        self.assertEqual(
            response.data,
            {
                "example": "http://testserver/namespaced/example/",
            }
        )

    def test_retrieve_non_namespaced_root(self):
        response = self.client.get('/non-namespaced/')
        self.assertEqual(
            response.data,
            {
                "example": "http://testserver/non-namespaced/example/",
            }
        )


class TestCustomLookupFields(TestCase):
    """
    Ensure that custom lookup fields are correctly routed.
    """
    urls = 'tests.test_routers'

    def setUp(self):
        RouterTestModel.objects.create(uuid='123', text='foo bar')

    def test_custom_lookup_field_route(self):
        detail_route = notes_router.urls[-1]
        detail_url_pattern = detail_route.regex.pattern
        self.assertIn('<uuid>', detail_url_pattern)

    def test_retrieve_lookup_field_list_view(self):
        response = self.client.get('/example/notes/')
        self.assertEqual(
            response.data,
            [{
                "url": "http://testserver/example/notes/123/",
                "uuid": "123", "text": "foo bar"
            }]
        )

    def test_retrieve_lookup_field_detail_view(self):
        response = self.client.get('/example/notes/123/')
        self.assertEqual(
            response.data,
            {
                "url": "http://testserver/example/notes/123/",
                "uuid": "123", "text": "foo bar"
            }
        )


class TestLookupValueRegex(TestCase):
    """
    Ensure the router honors lookup_value_regex when applied
    to the viewset.
    """
    def setUp(self):
        class NoteViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.objects.all()
            lookup_field = 'uuid'
            lookup_value_regex = '[0-9a-f]{32}'

        self.router = SimpleRouter()
        self.router.register(r'notes', NoteViewSet)
        self.urls = self.router.urls

    def test_urls_limited_by_lookup_value_regex(self):
        expected = ['^notes/$', '^notes/(?P<uuid>[0-9a-f]{32})/$']
        for idx in range(len(expected)):
            self.assertEqual(expected[idx], self.urls[idx].regex.pattern)


class TestTrailingSlashIncluded(TestCase):
    def setUp(self):
        class NoteViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.objects.all()

        self.router = SimpleRouter()
        self.router.register(r'notes', NoteViewSet)
        self.urls = self.router.urls

    def test_urls_have_trailing_slash_by_default(self):
        expected = ['^notes/$', '^notes/(?P<pk>[^/.]+)/$']
        for idx in range(len(expected)):
            self.assertEqual(expected[idx], self.urls[idx].regex.pattern)


class TestTrailingSlashRemoved(TestCase):
    def setUp(self):
        class NoteViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.objects.all()

        self.router = SimpleRouter(trailing_slash=False)
        self.router.register(r'notes', NoteViewSet)
        self.urls = self.router.urls

    def test_urls_can_have_trailing_slash_removed(self):
        expected = ['^notes$', '^notes/(?P<pk>[^/.]+)$']
        for idx in range(len(expected)):
            self.assertEqual(expected[idx], self.urls[idx].regex.pattern)


class TestNameableRoot(TestCase):
    def setUp(self):
        class NoteViewSet(viewsets.ModelViewSet):
            queryset = RouterTestModel.objects.all()

        self.router = DefaultRouter()
        self.router.root_view_name = 'nameable-root'
        self.router.register(r'notes', NoteViewSet)
        self.urls = self.router.urls

    def test_router_has_custom_name(self):
        expected = 'nameable-root'
        self.assertEqual(expected, self.urls[0].name)


class TestActionKeywordArgs(TestCase):
    """
    Ensure keyword arguments passed in the `@action` decorator
    are properly handled.  Refs #940.
    """

    def setUp(self):
        class TestViewSet(viewsets.ModelViewSet):
            permission_classes = []

            @detail_route(methods=['post'], permission_classes=[permissions.AllowAny])
            def custom(self, request, *args, **kwargs):
                return Response({
                    'permission_classes': self.permission_classes
                })

        self.router = SimpleRouter()
        self.router.register(r'test', TestViewSet, base_name='test')
        self.view = self.router.urls[-1].callback

    def test_action_kwargs(self):
        request = factory.post('/test/0/custom/')
        response = self.view(request)
        self.assertEqual(
            response.data,
            {'permission_classes': [permissions.AllowAny]}
        )


class TestActionAppliedToExistingRoute(TestCase):
    """
    Ensure `@detail_route` decorator raises an except when applied
    to an existing route
    """

    def test_exception_raised_when_action_applied_to_existing_route(self):
        class TestViewSet(viewsets.ModelViewSet):

            @detail_route(methods=['post'])
            def retrieve(self, request, *args, **kwargs):
                return Response({
                    'hello': 'world'
                })

        self.router = SimpleRouter()
        self.router.register(r'test', TestViewSet, base_name='test')

        with self.assertRaises(ImproperlyConfigured):
            self.router.urls


class DynamicListAndDetailViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'method': 'list'})

    @list_route(methods=['post'])
    def list_route_post(self, request, *args, **kwargs):
        return Response({'method': 'action1'})

    @detail_route(methods=['post'])
    def detail_route_post(self, request, *args, **kwargs):
        return Response({'method': 'action2'})

    @list_route()
    def list_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link1'})

    @detail_route()
    def detail_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link2'})

    @list_route(url_path="list_custom-route")
    def list_custom_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link1'})

    @detail_route(url_path="detail_custom-route")
    def detail_custom_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link2'})


class SubDynamicListAndDetailViewSet(DynamicListAndDetailViewSet):
    pass


class TestDynamicListAndDetailRouter(TestCase):
    def setUp(self):
        self.router = SimpleRouter()

    def _test_list_and_detail_route_decorators(self, viewset):
        routes = self.router.get_routes(viewset)
        decorator_routes = [r for r in routes if not (r.name.endswith('-list') or r.name.endswith('-detail'))]

        MethodNamesMap = namedtuple('MethodNamesMap', 'method_name url_path')
        # Make sure all these endpoints exist and none have been clobbered
        for i, endpoint in enumerate([MethodNamesMap('list_custom_route_get', 'list_custom-route'),
                                      MethodNamesMap('list_route_get', 'list_route_get'),
                                      MethodNamesMap('list_route_post', 'list_route_post'),
                                      MethodNamesMap('detail_custom_route_get', 'detail_custom-route'),
                                      MethodNamesMap('detail_route_get', 'detail_route_get'),
                                      MethodNamesMap('detail_route_post', 'detail_route_post')
                                      ]):
            route = decorator_routes[i]
            # check url listing
            method_name = endpoint.method_name
            url_path = endpoint.url_path

            if method_name.startswith('list_'):
                self.assertEqual(route.url,
                                 '^{{prefix}}/{0}{{trailing_slash}}$'.format(url_path))
            else:
                self.assertEqual(route.url,
                                 '^{{prefix}}/{{lookup}}/{0}{{trailing_slash}}$'.format(url_path))
            # check method to function mapping
            if method_name.endswith('_post'):
                method_map = 'post'
            else:
                method_map = 'get'
            self.assertEqual(route.mapping[method_map], method_name)

    def test_list_and_detail_route_decorators(self):
        self._test_list_and_detail_route_decorators(DynamicListAndDetailViewSet)

    def test_inherited_list_and_detail_route_decorators(self):
        self._test_list_and_detail_route_decorators(SubDynamicListAndDetailViewSet)
