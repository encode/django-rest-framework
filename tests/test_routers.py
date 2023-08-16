from collections import namedtuple

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase, override_settings
from django.urls import include, path, resolve, reverse

from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter, SimpleRouter
from rest_framework.test import (
    APIClient, APIRequestFactory, URLPatternsTestCase
)
from rest_framework.utils import json

factory = APIRequestFactory()


class RouterTestModel(models.Model):
    uuid = models.CharField(max_length=20)
    text = models.CharField(max_length=200)


class BasenameTestModel(models.Model):
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


class KWargedNoteViewSet(viewsets.ModelViewSet):
    queryset = RouterTestModel.objects.all()
    serializer_class = NoteSerializer
    lookup_field = 'text__contains'
    lookup_url_kwarg = 'text'


class BasenameViewSet(viewsets.ModelViewSet):
    queryset = BasenameTestModel.objects.all()
    serializer_class = None


class MockViewSet(viewsets.ModelViewSet):
    queryset = None
    serializer_class = None


class EmptyPrefixSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = RouterTestModel
        fields = ('uuid', 'text')


class EmptyPrefixViewSet(viewsets.ModelViewSet):
    queryset = [RouterTestModel(id=1, uuid='111', text='First'), RouterTestModel(id=2, uuid='222', text='Second')]
    serializer_class = EmptyPrefixSerializer

    def get_object(self, *args, **kwargs):
        index = int(self.kwargs['pk']) - 1
        return self.queryset[index]


class RegexUrlPathViewSet(viewsets.ViewSet):
    @action(detail=False, url_path='list/(?P<kwarg>[0-9]{4})')
    def regex_url_path_list(self, request, *args, **kwargs):
        kwarg = self.kwargs.get('kwarg', '')
        return Response({'kwarg': kwarg})

    @action(detail=True, url_path='detail/(?P<kwarg>[0-9]{4})')
    def regex_url_path_detail(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk', '')
        kwarg = self.kwargs.get('kwarg', '')
        return Response({'pk': pk, 'kwarg': kwarg})


class UrlPathViewSet(viewsets.ViewSet):
    @action(detail=False, url_path='list/<int:kwarg>')
    def url_path_list(self, request, *args, **kwargs):
        kwarg = self.kwargs.get('kwarg', '')
        return Response({'kwarg': kwarg})

    @action(detail=True, url_path='detail/<int:kwarg>')
    def url_path_detail(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk', '')
        kwarg = self.kwargs.get('kwarg', '')
        return Response({'pk': pk, 'kwarg': kwarg})

    @action(detail=True, url_path='detail/<int:kwarg>/detail/<int:param>')
    def url_path_detail_multiple_params(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk', '')
        kwarg = self.kwargs.get('kwarg', '')
        param = self.kwargs.get('param', '')
        return Response({'pk': pk, 'kwarg': kwarg, 'param': param})


notes_router = SimpleRouter()
notes_router.register(r'notes', NoteViewSet)

notes_path_router = SimpleRouter(use_regex_path=False)
notes_path_router.register('notes', NoteViewSet)

notes_path_default_router = DefaultRouter(use_regex_path=False)
notes_path_default_router.register('notes', NoteViewSet)

kwarged_notes_router = SimpleRouter()
kwarged_notes_router.register(r'notes', KWargedNoteViewSet)

namespaced_router = DefaultRouter()
namespaced_router.register(r'example', MockViewSet, basename='example')

empty_prefix_router = SimpleRouter()
empty_prefix_router.register(r'', EmptyPrefixViewSet, basename='empty_prefix')

regex_url_path_router = SimpleRouter()
regex_url_path_router.register(r'', RegexUrlPathViewSet, basename='regex')

url_path_router = SimpleRouter(use_regex_path=False)
url_path_router.register('', UrlPathViewSet, basename='path')


class BasicViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'method': 'list'})

    @action(methods=['post'], detail=True)
    def action1(self, request, *args, **kwargs):
        return Response({'method': 'action1'})

    @action(methods=['post', 'delete'], detail=True)
    def action2(self, request, *args, **kwargs):
        return Response({'method': 'action2'})

    @action(methods=['post'], detail=True)
    def action3(self, request, pk, *args, **kwargs):
        return Response({'post': pk})

    @action3.mapping.delete
    def action3_delete(self, request, pk, *args, **kwargs):
        return Response({'delete': pk})


class TestSimpleRouter(URLPatternsTestCase, TestCase):
    router = SimpleRouter()
    router.register('basics', BasicViewSet, basename='basic')

    urlpatterns = [
        path('api/', include(router.urls)),
    ]

    def setUp(self):
        self.router = SimpleRouter()

    def test_action_routes(self):
        # Get action routes (first two are list/detail)
        routes = self.router.get_routes(BasicViewSet)[2:]

        assert routes[0].url == '^{prefix}/{lookup}/action1{trailing_slash}$'
        assert routes[0].mapping == {
            'post': 'action1',
        }

        assert routes[1].url == '^{prefix}/{lookup}/action2{trailing_slash}$'
        assert routes[1].mapping == {
            'post': 'action2',
            'delete': 'action2',
        }

        assert routes[2].url == '^{prefix}/{lookup}/action3{trailing_slash}$'
        assert routes[2].mapping == {
            'post': 'action3',
            'delete': 'action3_delete',
        }

    def test_multiple_action_handlers(self):
        # Standard action
        response = self.client.post(reverse('basic-action3', args=[1]))
        assert response.data == {'post': '1'}

        # Additional handler registered with MethodMapper
        response = self.client.delete(reverse('basic-action3', args=[1]))
        assert response.data == {'delete': '1'}

    def test_register_after_accessing_urls(self):
        self.router.register(r'notes', NoteViewSet)
        assert len(self.router.urls) == 2  # list and detail
        self.router.register(r'notes_bis', NoteViewSet, basename='notes_bis')
        assert len(self.router.urls) == 4


class TestRootView(URLPatternsTestCase, TestCase):
    urlpatterns = [
        path('non-namespaced/', include(namespaced_router.urls)),
        path('namespaced/', include((namespaced_router.urls, 'namespaced'), namespace='namespaced')),
    ]

    def test_retrieve_namespaced_root(self):
        response = self.client.get('/namespaced/')
        assert response.data == {"example": "http://testserver/namespaced/example/"}

    def test_retrieve_non_namespaced_root(self):
        response = self.client.get('/non-namespaced/')
        assert response.data == {"example": "http://testserver/non-namespaced/example/"}


class TestCustomLookupFields(URLPatternsTestCase, TestCase):
    """
    Ensure that custom lookup fields are correctly routed.
    """
    urlpatterns = [
        path('example/', include(notes_router.urls)),
        path('example2/', include(kwarged_notes_router.urls)),
    ]

    def setUp(self):
        RouterTestModel.objects.create(uuid='123', text='foo bar')
        RouterTestModel.objects.create(uuid='a b', text='baz qux')

    def test_custom_lookup_field_route(self):
        detail_route = notes_router.urls[-1]
        assert '<uuid>' in detail_route.pattern.regex.pattern

    def test_retrieve_lookup_field_list_view(self):
        response = self.client.get('/example/notes/')
        assert response.data == [
            {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"},
            {"url": "http://testserver/example/notes/a%20b/", "uuid": "a b", "text": "baz qux"},
        ]

    def test_retrieve_lookup_field_detail_view(self):
        response = self.client.get('/example/notes/123/')
        assert response.data == {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"}

    def test_retrieve_lookup_field_url_encoded_detail_view_(self):
        response = self.client.get('/example/notes/a%20b/')
        assert response.data == {"url": "http://testserver/example/notes/a%20b/", "uuid": "a b", "text": "baz qux"}


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
            assert expected[idx] == self.urls[idx].pattern.regex.pattern


@override_settings(ROOT_URLCONF='tests.test_routers')
class TestLookupUrlKwargs(URLPatternsTestCase, TestCase):
    """
    Ensure the router honors lookup_url_kwarg.

    Setup a deep lookup_field, but map it to a simple URL kwarg.
    """
    urlpatterns = [
        path('example/', include(notes_router.urls)),
        path('example2/', include(kwarged_notes_router.urls)),
    ]

    def setUp(self):
        RouterTestModel.objects.create(uuid='123', text='foo bar')

    def test_custom_lookup_url_kwarg_route(self):
        detail_route = kwarged_notes_router.urls[-1]
        assert '^notes/(?P<text>' in detail_route.pattern.regex.pattern

    def test_retrieve_lookup_url_kwarg_detail_view(self):
        response = self.client.get('/example2/notes/fo/')
        assert response.data == {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"}

    def test_retrieve_lookup_url_encoded_kwarg_detail_view(self):
        response = self.client.get('/example2/notes/foo%20bar/')
        assert response.data == {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"}


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
            assert expected[idx] == self.urls[idx].pattern.regex.pattern


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
            assert expected[idx] == self.urls[idx].pattern.regex.pattern


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
        assert expected == self.urls[-1].name


class TestActionKeywordArgs(TestCase):
    """
    Ensure keyword arguments passed in the `@action` decorator
    are properly handled.  Refs #940.
    """

    def setUp(self):
        class TestViewSet(viewsets.ModelViewSet):
            permission_classes = []

            @action(methods=['post'], detail=True, permission_classes=[permissions.AllowAny])
            def custom(self, request, *args, **kwargs):
                return Response({
                    'permission_classes': self.permission_classes
                })

        self.router = SimpleRouter()
        self.router.register(r'test', TestViewSet, basename='test')
        self.view = self.router.urls[-1].callback

    def test_action_kwargs(self):
        request = factory.post('/test/0/custom/')
        response = self.view(request)
        assert response.data == {'permission_classes': [permissions.AllowAny]}


class TestActionAppliedToExistingRoute(TestCase):
    """
    Ensure `@action` decorator raises an except when applied
    to an existing route
    """

    def test_exception_raised_when_action_applied_to_existing_route(self):
        class TestViewSet(viewsets.ModelViewSet):

            @action(methods=['post'], detail=True)
            def retrieve(self, request, *args, **kwargs):
                return Response({
                    'hello': 'world'
                })

        self.router = SimpleRouter()
        self.router.register(r'test', TestViewSet, basename='test')

        with pytest.raises(ImproperlyConfigured):
            self.router.urls


class DynamicListAndDetailViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        return Response({'method': 'list'})

    @action(methods=['post'], detail=False)
    def list_route_post(self, request, *args, **kwargs):
        return Response({'method': 'action1'})

    @action(methods=['post'], detail=True)
    def detail_route_post(self, request, *args, **kwargs):
        return Response({'method': 'action2'})

    @action(detail=False)
    def list_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link1'})

    @action(detail=True)
    def detail_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link2'})

    @action(detail=False, url_path="list_custom-route")
    def list_custom_route_get(self, request, *args, **kwargs):
        return Response({'method': 'link1'})

    @action(detail=True, url_path="detail_custom-route")
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
                assert route.url == '^{{prefix}}/{0}{{trailing_slash}}$'.format(url_path)
            else:
                assert route.url == '^{{prefix}}/{{lookup}}/{0}{{trailing_slash}}$'.format(url_path)
            # check method to function mapping
            if method_name.endswith('_post'):
                method_map = 'post'
            else:
                method_map = 'get'
            assert route.mapping[method_map] == method_name

    def test_list_and_detail_route_decorators(self):
        self._test_list_and_detail_route_decorators(DynamicListAndDetailViewSet)

    def test_inherited_list_and_detail_route_decorators(self):
        self._test_list_and_detail_route_decorators(SubDynamicListAndDetailViewSet)


class TestEmptyPrefix(URLPatternsTestCase, TestCase):
    urlpatterns = [
        path('empty-prefix/', include(empty_prefix_router.urls)),
    ]

    def test_empty_prefix_list(self):
        response = self.client.get('/empty-prefix/')
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == [{'uuid': '111', 'text': 'First'},
                                                         {'uuid': '222', 'text': 'Second'}]

    def test_empty_prefix_detail(self):
        response = self.client.get('/empty-prefix/1/')
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'uuid': '111', 'text': 'First'}


class TestRegexUrlPath(URLPatternsTestCase, TestCase):
    urlpatterns = [
        path('regex/', include(regex_url_path_router.urls)),
    ]

    def test_regex_url_path_list(self):
        kwarg = '1234'
        response = self.client.get('/regex/list/{}/'.format(kwarg))
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'kwarg': kwarg}

    def test_regex_url_path_detail(self):
        pk = '1'
        kwarg = '1234'
        response = self.client.get('/regex/{}/detail/{}/'.format(pk, kwarg))
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'pk': pk, 'kwarg': kwarg}


class TestUrlPath(URLPatternsTestCase, TestCase):
    client_class = APIClient
    urlpatterns = [
        path('path/', include(url_path_router.urls)),
        path('default/', include(notes_path_default_router.urls)),
        path('example/', include(notes_path_router.urls)),
    ]

    def setUp(self):
        RouterTestModel.objects.create(uuid='123', text='foo bar')
        RouterTestModel.objects.create(uuid='a b', text='baz qux')

    def test_create(self):
        new_note = {
            'uuid': 'foo',
            'text': 'example'
        }
        response = self.client.post('/example/notes/', data=new_note)
        assert response.status_code == 201
        assert response['location'] == 'http://testserver/example/notes/foo/'
        assert response.data == {"url": "http://testserver/example/notes/foo/", "uuid": "foo", "text": "example"}
        assert RouterTestModel.objects.filter(uuid='foo').exists()

    def test_retrieve(self):
        for url in ('/example/notes/123/', '/default/notes/123/'):
            with self.subTest(url=url):
                response = self.client.get(url)
                assert response.status_code == 200
                # only gets example path since was the last to be registered
                assert response.data == {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"}

    def test_list(self):
        for url in ('/example/notes/', '/default/notes/'):
            with self.subTest(url=url):
                response = self.client.get(url)
                assert response.status_code == 200
                # only gets example path since was the last to be registered
                assert response.data == [
                    {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar"},
                    {"url": "http://testserver/example/notes/a%20b/", "uuid": "a b", "text": "baz qux"},
                ]

    def test_update(self):
        updated_note = {
            'text': 'foo bar example'
        }
        response = self.client.patch('/example/notes/123/', data=updated_note)
        assert response.status_code == 200
        assert response.data == {"url": "http://testserver/example/notes/123/", "uuid": "123", "text": "foo bar example"}

    def test_delete(self):
        response = self.client.delete('/example/notes/123/')
        assert response.status_code == 204
        assert not RouterTestModel.objects.filter(uuid='123').exists()

    def test_list_extra_action(self):
        kwarg = 1234
        response = self.client.get('/path/list/{}/'.format(kwarg))
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'kwarg': kwarg}

    def test_detail_extra_action(self):
        pk = '1'
        kwarg = 1234
        response = self.client.get('/path/{}/detail/{}/'.format(pk, kwarg))
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'pk': pk, 'kwarg': kwarg}

    def test_detail_extra_other_action(self):
        # this to assure that ambiguous patterns are interpreted correctly
        # using the `path` converters this URL is recognized to match the pattern
        # of `UrlPathViewSet.url_path_detail` when it should match
        # `UrlPathViewSet.url_path_detail_multiple_params`
        pk = '1'
        kwarg = 1234
        param = 2
        response = self.client.get('/path/1/detail/1234/detail/2/')
        assert response.status_code == 200
        assert json.loads(response.content.decode()) == {'pk': pk, 'kwarg': kwarg, 'param': param}

    def test_defaultrouter_root(self):
        response = self.client.get('/default/')
        assert response.status_code == 200
        # only gets example path since was the last to be registered
        assert response.data == {"notes": "http://testserver/example/notes/"}


class TestViewInitkwargs(URLPatternsTestCase, TestCase):
    urlpatterns = [
        path('example/', include(notes_router.urls)),
    ]

    def test_suffix(self):
        match = resolve('/example/notes/')
        initkwargs = match.func.initkwargs

        assert initkwargs['suffix'] == 'List'

    def test_detail(self):
        match = resolve('/example/notes/')
        initkwargs = match.func.initkwargs

        assert not initkwargs['detail']

    def test_basename(self):
        match = resolve('/example/notes/')
        initkwargs = match.func.initkwargs

        assert initkwargs['basename'] == 'routertestmodel'


class BasenameTestCase:
    def test_conflicting_autogenerated_basenames(self):
        """
        Ensure 2 routers with the same model, and no basename specified
        throws an ImproperlyConfigured exception
        """
        self.router.register(r'notes', NoteViewSet)

        with pytest.raises(ImproperlyConfigured):
            self.router.register(r'notes_kwduplicate', KWargedNoteViewSet)

        with pytest.raises(ImproperlyConfigured):
            self.router.register(r'notes_duplicate', NoteViewSet)

    def test_conflicting_mixed_basenames(self):
        """
        Ensure 2 routers with the same model, and no basename specified on 1
        throws an ImproperlyConfigured exception
        """
        self.router.register(r'notes', NoteViewSet)

        with pytest.raises(ImproperlyConfigured):
            self.router.register(r'notes_kwduplicate', KWargedNoteViewSet, basename='routertestmodel')

        with pytest.raises(ImproperlyConfigured):
            self.router.register(r'notes_duplicate', NoteViewSet, basename='routertestmodel')

    def test_nonconflicting_mixed_basenames(self):
        """
        Ensure 2 routers with the same model, and a distinct basename
        specified on the second router does not fail
        """
        self.router.register(r'notes', NoteViewSet)
        self.router.register(r'notes_kwduplicate', KWargedNoteViewSet, basename='routertestmodel_kwduplicate')
        self.router.register(r'notes_duplicate', NoteViewSet, basename='routertestmodel_duplicate')

    def test_conflicting_specified_basename(self):
        """
        Ensure 2 routers with the same model, and the same basename specified
        on both throws an ImproperlyConfigured exception
        """
        self.router.register(r'notes', NoteViewSet, basename='notes')

        with pytest.raises(ImproperlyConfigured):
            self.router.register(r'notes_kwduplicate', KWargedNoteViewSet, basename='notes')

        with pytest.raises(ImproperlyConfigured):
            self.router.register(r'notes_duplicate', KWargedNoteViewSet, basename='notes')

    def test_nonconflicting_specified_basename(self):
        """
        Ensure 2 routers with the same model, and a distinct basename specified
        on each does not throw an exception
        """
        self.router.register(r'notes', NoteViewSet, basename='notes')
        self.router.register(r'notes_kwduplicate', KWargedNoteViewSet, basename='notes_kwduplicate')
        self.router.register(r'notes_duplicate', NoteViewSet, basename='notes_duplicate')

    def test_nonconflicting_specified_basename_different_models(self):
        """
        Ensure 2 routers with different models, and a distinct basename specified
        on each does not throw an exception
        """
        self.router.register(r'notes', NoteViewSet, basename='notes')
        self.router.register(r'notes_basename', BasenameViewSet, basename='notes_basename')

    def test_conflicting_specified_basename_different_models(self):
        """
        Ensure 2 routers with different models, and a conflicting basename specified
        throws an exception
        """
        self.router.register(r'notes', NoteViewSet)
        with pytest.raises(ImproperlyConfigured):
            self.router.register(r'notes_basename', BasenameViewSet, basename='routertestmodel')

    def test_nonconflicting_autogenerated_basename_different_models(self):
        """
        Ensure 2 routers with different models, and a distinct basename specified
        on each does not throw an exception
        """
        self.router.register(r'notes', NoteViewSet)
        self.router.register(r'notes_basename', BasenameViewSet)


class TestDuplicateBasenameSimpleRouter(BasenameTestCase, TestCase):
    def setUp(self):
        self.router = SimpleRouter(trailing_slash=False)


class TestDuplicateBasenameDefaultRouter(BasenameTestCase, TestCase):
    def setUp(self):
        self.router = DefaultRouter()


class TestDuplicateBasenameDefaultRouterRootViewName(BasenameTestCase, TestCase):
    def setUp(self):
        self.router = DefaultRouter()
        self.router.root_view_name = 'nameable-root'
