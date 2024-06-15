import re
from collections.abc import MutableMapping

import pytest
from django.core.cache import cache
from django.db import models
from django.http.request import HttpRequest
from django.template import loader
from django.test import TestCase, override_settings
from django.urls import include, path, re_path
from django.utils.safestring import SafeText
from django.utils.translation import gettext_lazy as _

from rest_framework import permissions, serializers, status
from rest_framework.compat import coreapi
from rest_framework.decorators import action
from rest_framework.renderers import (
    AdminRenderer, BaseRenderer, BrowsableAPIRenderer, DocumentationRenderer,
    HTMLFormRenderer, JSONRenderer, SchemaJSRenderer, StaticHTMLRenderer
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory, URLPatternsTestCase
from rest_framework.utils import json
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

DUMMYSTATUS = status.HTTP_200_OK
DUMMYCONTENT = 'dummycontent'


def RENDERER_A_SERIALIZER(x):
    return ('Renderer A: %s' % x).encode('ascii')


def RENDERER_B_SERIALIZER(x):
    return ('Renderer B: %s' % x).encode('ascii')


expected_results = [
    ((elem for elem in [1, 2, 3]), JSONRenderer, b'[1,2,3]')  # Generator
]


class DummyTestModel(models.Model):
    name = models.CharField(max_length=42, default='')


class BasicRendererTests(TestCase):
    def test_expected_results(self):
        for value, renderer_cls, expected in expected_results:
            output = renderer_cls().render(value)
            self.assertEqual(output, expected)


class RendererA(BaseRenderer):
    media_type = 'mock/renderera'
    format = "formata"

    def render(self, data, media_type=None, renderer_context=None):
        return RENDERER_A_SERIALIZER(data)


class RendererB(BaseRenderer):
    media_type = 'mock/rendererb'
    format = "formatb"

    def render(self, data, media_type=None, renderer_context=None):
        return RENDERER_B_SERIALIZER(data)


class MockView(APIView):
    renderer_classes = (RendererA, RendererB)

    def get(self, request, **kwargs):
        return Response(DUMMYCONTENT, status=DUMMYSTATUS)


class MockGETView(APIView):
    def get(self, request, **kwargs):
        return Response({'foo': ['bar', 'baz']})


class MockPOSTView(APIView):
    def post(self, request, **kwargs):
        return Response({'foo': request.data})


class EmptyGETView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, **kwargs):
        return Response(status=status.HTTP_204_NO_CONTENT)


class HTMLView(APIView):
    renderer_classes = (BrowsableAPIRenderer, )

    def get(self, request, **kwargs):
        return Response('text')


class HTMLView1(APIView):
    renderer_classes = (BrowsableAPIRenderer, JSONRenderer)

    def get(self, request, **kwargs):
        return Response('text')


urlpatterns = [
    re_path(r'^.*\.(?P<format>.+)$', MockView.as_view(renderer_classes=[RendererA, RendererB])),
    path('', MockView.as_view(renderer_classes=[RendererA, RendererB])),
    path('cache', MockGETView.as_view()),
    path('parseerror', MockPOSTView.as_view(renderer_classes=[JSONRenderer, BrowsableAPIRenderer])),
    path('html', HTMLView.as_view()),
    path('html1', HTMLView1.as_view()),
    path('empty', EmptyGETView.as_view()),
    path('api', include('rest_framework.urls', namespace='rest_framework'))
]


class POSTDeniedPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method != 'POST'


class POSTDeniedView(APIView):
    renderer_classes = (BrowsableAPIRenderer,)
    permission_classes = (POSTDeniedPermission,)

    def get(self, request):
        return Response()

    def post(self, request):
        return Response()

    def put(self, request):
        return Response()

    def patch(self, request):
        return Response()


class DocumentingRendererTests(TestCase):
    def test_only_permitted_forms_are_displayed(self):
        view = POSTDeniedView.as_view()
        request = APIRequestFactory().get('/')
        response = view(request).render()
        self.assertNotContains(response, '>POST<')
        self.assertContains(response, '>PUT<')
        self.assertContains(response, '>PATCH<')


@override_settings(ROOT_URLCONF='tests.test_renderers')
class RendererEndToEndTests(TestCase):
    """
    End-to-end testing of renderers using an RendererMixin on a generic view.
    """
    def test_default_renderer_serializes_content(self):
        """If the Accept header is not set the default renderer should serialize the response."""
        resp = self.client.get('/')
        self.assertEqual(resp['Content-Type'], RendererA.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, RENDERER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEqual(resp.status_code, DUMMYSTATUS)

    def test_head_method_serializes_no_content(self):
        """No response must be included in HEAD requests."""
        resp = self.client.head('/')
        self.assertEqual(resp.status_code, DUMMYSTATUS)
        self.assertEqual(resp['Content-Type'], RendererA.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, b'')

    def test_default_renderer_serializes_content_on_accept_any(self):
        """If the Accept header is set to */* the default renderer should serialize the response."""
        resp = self.client.get('/', HTTP_ACCEPT='*/*')
        self.assertEqual(resp['Content-Type'], RendererA.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, RENDERER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEqual(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_serializes_content_default_case(self):
        """If the Accept header is set the specified renderer should serialize the response.
        (In this case we check that works for the default renderer)"""
        resp = self.client.get('/', HTTP_ACCEPT=RendererA.media_type)
        self.assertEqual(resp['Content-Type'], RendererA.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, RENDERER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEqual(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_serializes_content_non_default_case(self):
        """If the Accept header is set the specified renderer should serialize the response.
        (In this case we check that works for a non-default renderer)"""
        resp = self.client.get('/', HTTP_ACCEPT=RendererB.media_type)
        self.assertEqual(resp['Content-Type'], RendererB.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEqual(resp.status_code, DUMMYSTATUS)

    def test_unsatisfiable_accept_header_on_request_returns_406_status(self):
        """If the Accept header is unsatisfiable we should return a 406 Not Acceptable response."""
        resp = self.client.get('/', HTTP_ACCEPT='foo/bar')
        self.assertEqual(resp.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_specified_renderer_serializes_content_on_format_query(self):
        """If a 'format' query is specified, the renderer with the matching
        format attribute should serialize the response."""
        param = '?%s=%s' % (
            api_settings.URL_FORMAT_OVERRIDE,
            RendererB.format
        )
        resp = self.client.get('/' + param)
        self.assertEqual(resp['Content-Type'], RendererB.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEqual(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_serializes_content_on_format_kwargs(self):
        """If a 'format' keyword arg is specified, the renderer with the matching
        format attribute should serialize the response."""
        resp = self.client.get('/something.formatb')
        self.assertEqual(resp['Content-Type'], RendererB.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEqual(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_is_used_on_format_query_with_matching_accept(self):
        """If both a 'format' query and a matching Accept header specified,
        the renderer with the matching format attribute should serialize the response."""
        param = '?%s=%s' % (
            api_settings.URL_FORMAT_OVERRIDE,
            RendererB.format
        )
        resp = self.client.get('/' + param,
                               HTTP_ACCEPT=RendererB.media_type)
        self.assertEqual(resp['Content-Type'], RendererB.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEqual(resp.status_code, DUMMYSTATUS)

    def test_parse_error_renderers_browsable_api(self):
        """Invalid data should still render the browsable API correctly."""
        resp = self.client.post('/parseerror', data='foobar', content_type='application/json', HTTP_ACCEPT='text/html')
        self.assertEqual(resp['Content-Type'], 'text/html; charset=utf-8')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_204_no_content_responses_have_no_content_type_set(self):
        """
        Regression test for #1196

        https://github.com/encode/django-rest-framework/issues/1196
        """
        resp = self.client.get('/empty')
        self.assertEqual(resp.get('Content-Type', None), None)
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_contains_headers_of_api_response(self):
        """
        Issue #1437

        Test we display the headers of the API response and not those from the
        HTML response
        """
        resp = self.client.get('/html1')
        self.assertContains(resp, '>GET, HEAD, OPTIONS<')
        self.assertContains(resp, '>application/json<')
        self.assertNotContains(resp, '>text/html; charset=utf-8<')


_flat_repr = '{"foo":["bar","baz"]}'
_indented_repr = '{\n  "foo": [\n    "bar",\n    "baz"\n  ]\n}'


def strip_trailing_whitespace(content):
    """
    Seems to be some inconsistencies re. trailing whitespace with
    different versions of the json lib.
    """
    return re.sub(' +\n', '\n', content)


class BaseRendererTests(TestCase):
    """
    Tests BaseRenderer
    """
    def test_render_raise_error(self):
        """
        BaseRenderer.render should raise NotImplementedError
        """
        with pytest.raises(NotImplementedError):
            BaseRenderer().render('test')


class JSONRendererTests(TestCase):
    """
    Tests specific to the JSON Renderer
    """

    def test_render_lazy_strings(self):
        """
        JSONRenderer should deal with lazy translated strings.
        """
        ret = JSONRenderer().render(_('test'))
        self.assertEqual(ret, b'"test"')

    def test_render_queryset_values(self):
        o = DummyTestModel.objects.create(name='dummy')
        qs = DummyTestModel.objects.values('id', 'name')
        ret = JSONRenderer().render(qs)
        data = json.loads(ret.decode())
        self.assertEqual(data, [{'id': o.id, 'name': o.name}])

    def test_render_queryset_values_list(self):
        o = DummyTestModel.objects.create(name='dummy')
        qs = DummyTestModel.objects.values_list('id', 'name')
        ret = JSONRenderer().render(qs)
        data = json.loads(ret.decode())
        self.assertEqual(data, [[o.id, o.name]])

    def test_render_dict_abc_obj(self):
        class Dict(MutableMapping):
            def __init__(self):
                self._dict = {}

            def __getitem__(self, key):
                return self._dict.__getitem__(key)

            def __setitem__(self, key, value):
                return self._dict.__setitem__(key, value)

            def __delitem__(self, key):
                return self._dict.__delitem__(key)

            def __iter__(self):
                return self._dict.__iter__()

            def __len__(self):
                return self._dict.__len__()

            def keys(self):
                return self._dict.keys()

        x = Dict()
        x['key'] = 'string value'
        x[2] = 3
        ret = JSONRenderer().render(x)
        data = json.loads(ret.decode())
        self.assertEqual(data, {'key': 'string value', '2': 3})

    def test_render_obj_with_getitem(self):
        class DictLike:
            def __init__(self):
                self._dict = {}

            def set(self, value):
                self._dict = dict(value)

            def __getitem__(self, key):
                return self._dict[key]

        x = DictLike()
        x.set({'a': 1, 'b': 'string'})
        with self.assertRaises(TypeError):
            JSONRenderer().render(x)

    def test_float_strictness(self):
        renderer = JSONRenderer()

        # Default to strict
        for value in [float('inf'), float('-inf'), float('nan')]:
            with pytest.raises(ValueError):
                renderer.render(value)

        renderer.strict = False
        assert renderer.render(float('inf')) == b'Infinity'
        assert renderer.render(float('-inf')) == b'-Infinity'
        assert renderer.render(float('nan')) == b'NaN'

    def test_without_content_type_args(self):
        """
        Test basic JSON rendering.
        """
        obj = {'foo': ['bar', 'baz']}
        renderer = JSONRenderer()
        content = renderer.render(obj, 'application/json')
        # Fix failing test case which depends on version of JSON library.
        self.assertEqual(content.decode(), _flat_repr)

    def test_with_content_type_args(self):
        """
        Test JSON rendering with additional content type arguments supplied.
        """
        obj = {'foo': ['bar', 'baz']}
        renderer = JSONRenderer()
        content = renderer.render(obj, 'application/json; indent=2')
        self.assertEqual(strip_trailing_whitespace(content.decode()), _indented_repr)


class UnicodeJSONRendererTests(TestCase):
    """
    Tests specific for the Unicode JSON Renderer
    """
    def test_proper_encoding(self):
        obj = {'countries': ['United Kingdom', 'France', 'España']}
        renderer = JSONRenderer()
        content = renderer.render(obj, 'application/json')
        self.assertEqual(content, '{"countries":["United Kingdom","France","España"]}'.encode())

    def test_u2028_u2029(self):
        # The \u2028 and \u2029 characters should be escaped,
        # even when the non-escaping unicode representation is used.
        # Regression test for #2169
        obj = {'should_escape': '\u2028\u2029'}
        renderer = JSONRenderer()
        content = renderer.render(obj, 'application/json')
        self.assertEqual(content, '{"should_escape":"\\u2028\\u2029"}'.encode())


class AsciiJSONRendererTests(TestCase):
    """
    Tests specific for the Unicode JSON Renderer
    """
    def test_proper_encoding(self):
        class AsciiJSONRenderer(JSONRenderer):
            ensure_ascii = True
        obj = {'countries': ['United Kingdom', 'France', 'España']}
        renderer = AsciiJSONRenderer()
        content = renderer.render(obj, 'application/json')
        self.assertEqual(content, '{"countries":["United Kingdom","France","Espa\\u00f1a"]}'.encode())


# Tests for caching issue, #346
@override_settings(ROOT_URLCONF='tests.test_renderers')
class CacheRenderTest(TestCase):
    """
    Tests specific to caching responses
    """
    def test_head_caching(self):
        """
        Test caching of HEAD requests
        """
        response = self.client.head('/cache')
        cache.set('key', response)
        cached_response = cache.get('key')
        assert isinstance(cached_response, Response)
        assert cached_response.content == response.content
        assert cached_response.status_code == response.status_code

    def test_get_caching(self):
        """
        Test caching of GET requests
        """
        response = self.client.get('/cache')
        cache.set('key', response)
        cached_response = cache.get('key')
        assert isinstance(cached_response, Response)
        assert cached_response.content == response.content
        assert cached_response.status_code == response.status_code


class TestJSONIndentationStyles:
    def test_indented(self):
        renderer = JSONRenderer()
        data = {"a": 1, "b": 2}
        assert renderer.render(data) == b'{"a":1,"b":2}'

    def test_compact(self):
        renderer = JSONRenderer()
        data = {"a": 1, "b": 2}
        context = {'indent': 4}
        assert (
            renderer.render(data, renderer_context=context) ==
            b'{\n    "a": 1,\n    "b": 2\n}'
        )

    def test_long_form(self):
        renderer = JSONRenderer()
        renderer.compact = False
        data = {"a": 1, "b": 2}
        assert renderer.render(data) == b'{"a": 1, "b": 2}'


class TestHiddenFieldHTMLFormRenderer(TestCase):
    def test_hidden_field_rendering(self):
        class TestSerializer(serializers.Serializer):
            published = serializers.HiddenField(default=True)

        serializer = TestSerializer(data={})
        serializer.is_valid()
        renderer = HTMLFormRenderer()
        field = serializer['published']
        rendered = renderer.render_field(field, {})
        assert rendered == ''


class TestHTMLFormRenderer(TestCase):
    def setUp(self):
        class TestSerializer(serializers.Serializer):
            test_field = serializers.CharField()

        self.renderer = HTMLFormRenderer()
        self.serializer = TestSerializer(data={})

    def test_render_with_default_args(self):
        self.serializer.is_valid()
        renderer = HTMLFormRenderer()

        result = renderer.render(self.serializer.data)

        self.assertIsInstance(result, SafeText)

    def test_render_with_provided_args(self):
        self.serializer.is_valid()
        renderer = HTMLFormRenderer()

        result = renderer.render(self.serializer.data, None, {})

        self.assertIsInstance(result, SafeText)


class TestChoiceFieldHTMLFormRenderer(TestCase):
    """
    Test rendering ChoiceField with HTMLFormRenderer.
    """

    def setUp(self):
        choices = ((1, 'Option1'), (2, 'Option2'), (12, 'Option12'))

        class TestSerializer(serializers.Serializer):
            test_field = serializers.ChoiceField(choices=choices,
                                                 initial=2)

        self.TestSerializer = TestSerializer
        self.renderer = HTMLFormRenderer()

    def test_render_initial_option(self):
        serializer = self.TestSerializer()
        result = self.renderer.render(serializer.data)

        self.assertIsInstance(result, SafeText)

        self.assertInHTML('<option value="2" selected>Option2</option>',
                          result)
        self.assertInHTML('<option value="1">Option1</option>', result)
        self.assertInHTML('<option value="12">Option12</option>', result)

    def test_render_selected_option(self):
        serializer = self.TestSerializer(data={'test_field': '12'})

        serializer.is_valid()
        result = self.renderer.render(serializer.data)

        self.assertIsInstance(result, SafeText)

        self.assertInHTML('<option value="12" selected>Option12</option>',
                          result)
        self.assertInHTML('<option value="1">Option1</option>', result)
        self.assertInHTML('<option value="2">Option2</option>', result)


class TestMultipleChoiceFieldHTMLFormRenderer(TestCase):
    """
    Test rendering MultipleChoiceField with HTMLFormRenderer.
    """

    def setUp(self):
        self.renderer = HTMLFormRenderer()

    def test_render_selected_option_with_string_option_ids(self):
        choices = (('1', 'Option1'), ('2', 'Option2'), ('12', 'Option12'),
                   ('}', 'OptionBrace'))

        class TestSerializer(serializers.Serializer):
            test_field = serializers.MultipleChoiceField(choices=choices)

        serializer = TestSerializer(data={'test_field': ['12']})
        serializer.is_valid()

        result = self.renderer.render(serializer.data)

        self.assertIsInstance(result, SafeText)

        self.assertInHTML('<option value="12" selected>Option12</option>',
                          result)
        self.assertInHTML('<option value="1">Option1</option>', result)
        self.assertInHTML('<option value="2">Option2</option>', result)
        self.assertInHTML('<option value="}">OptionBrace</option>', result)

    def test_render_selected_option_with_integer_option_ids(self):
        choices = ((1, 'Option1'), (2, 'Option2'), (12, 'Option12'))

        class TestSerializer(serializers.Serializer):
            test_field = serializers.MultipleChoiceField(choices=choices)

        serializer = TestSerializer(data={'test_field': ['12']})
        serializer.is_valid()

        result = self.renderer.render(serializer.data)

        self.assertIsInstance(result, SafeText)

        self.assertInHTML('<option value="12" selected>Option12</option>',
                          result)
        self.assertInHTML('<option value="1">Option1</option>', result)
        self.assertInHTML('<option value="2">Option2</option>', result)


class StaticHTMLRendererTests(TestCase):
    """
    Tests specific for Static HTML Renderer
    """
    def setUp(self):
        self.renderer = StaticHTMLRenderer()

    def test_static_renderer(self):
        data = '<html><body>text</body></html>'
        result = self.renderer.render(data)
        assert result == data

    def test_static_renderer_with_exception(self):
        context = {
            'response': Response(status=500, exception=True),
            'request': Request(HttpRequest())
        }
        result = self.renderer.render({}, renderer_context=context)
        assert result == '500 Internal Server Error'


class BrowsableAPIRendererTests(URLPatternsTestCase):
    class ExampleViewSet(ViewSet):
        def list(self, request):
            return Response()

        @action(detail=False, name="Extra list action")
        def list_action(self, request):
            raise NotImplementedError

    class AuthExampleViewSet(ExampleViewSet):
        permission_classes = [permissions.IsAuthenticated]

    class SimpleSerializer(serializers.Serializer):
        name = serializers.CharField()

    router = SimpleRouter()
    router.register('examples', ExampleViewSet, basename='example')
    router.register('auth-examples', AuthExampleViewSet, basename='auth-example')
    urlpatterns = [path('api/', include(router.urls))]

    def setUp(self):
        self.renderer = BrowsableAPIRenderer()
        self.renderer.accepted_media_type = ''
        self.renderer.renderer_context = {}

    def test_render_form_for_serializer(self):
        with self.subTest('Serializer'):
            serializer = BrowsableAPIRendererTests.SimpleSerializer(data={'name': 'Name'})
            form = self.renderer.render_form_for_serializer(serializer)
            assert isinstance(form, str), 'Must return form for serializer'

        with self.subTest('ListSerializer'):
            list_serializer = BrowsableAPIRendererTests.SimpleSerializer(data=[{'name': 'Name'}], many=True)
            form = self.renderer.render_form_for_serializer(list_serializer)
            assert form is None, 'Must not return form for list serializer'

    def test_get_raw_data_form(self):
        with self.subTest('Serializer'):
            class DummyGenericViewsetLike(APIView):
                def get_serializer(self, **kwargs):
                    return BrowsableAPIRendererTests.SimpleSerializer(**kwargs)

                def get(self, request):
                    response = Response()
                    response.view = self
                    return response

                post = get

            view = DummyGenericViewsetLike.as_view()
            _request = APIRequestFactory().get('/')
            request = Request(_request)
            response = view(_request)
            view = response.view

            raw_data_form = self.renderer.get_raw_data_form({'name': 'Name'}, view, 'POST', request)
            assert raw_data_form['_content'].initial == '{\n    "name": ""\n}'

        with self.subTest('ListSerializer'):
            class DummyGenericViewsetLike(APIView):
                def get_serializer(self, **kwargs):
                    return BrowsableAPIRendererTests.SimpleSerializer(many=True, **kwargs)  # returns ListSerializer

                def get(self, request):
                    response = Response()
                    response.view = self
                    return response

                post = get

            view = DummyGenericViewsetLike.as_view()
            _request = APIRequestFactory().get('/')
            request = Request(_request)
            response = view(_request)
            view = response.view

            raw_data_form = self.renderer.get_raw_data_form([{'name': 'Name'}], view, 'POST', request)
            assert raw_data_form['_content'].initial == '[\n    {\n        "name": ""\n    }\n]'

    def test_get_description_returns_empty_string_for_401_and_403_statuses(self):
        assert self.renderer.get_description({}, status_code=401) == ''
        assert self.renderer.get_description({}, status_code=403) == ''

    def test_get_filter_form_returns_none_if_data_is_not_list_instance(self):
        class DummyView:
            get_queryset = None
            filter_backends = None

        result = self.renderer.get_filter_form(data='not list',
                                               view=DummyView(), request={})
        assert result is None

    def test_extra_actions_dropdown(self):
        resp = self.client.get('/api/examples/', HTTP_ACCEPT='text/html')
        assert 'id="extra-actions-menu"' in resp.content.decode()
        assert '/api/examples/list_action/' in resp.content.decode()
        assert '>Extra list action<' in resp.content.decode()

    def test_extra_actions_dropdown_not_authed(self):
        resp = self.client.get('/api/unauth-examples/', HTTP_ACCEPT='text/html')
        assert 'id="extra-actions-menu"' not in resp.content.decode()
        assert '/api/examples/list_action/' not in resp.content.decode()
        assert '>Extra list action<' not in resp.content.decode()


class AdminRendererTests(TestCase):

    def setUp(self):
        self.renderer = AdminRenderer()

    def test_render_when_resource_created(self):
        class DummyView(APIView):
            renderer_classes = (AdminRenderer, )
        request = Request(HttpRequest())
        request.build_absolute_uri = lambda: 'http://example.com'
        response = Response(status=201, headers={'Location': '/test'})
        context = {
            'view': DummyView(),
            'request': request,
            'response': response
        }

        result = self.renderer.render(data={'test': 'test'},
                                      renderer_context=context)
        assert result == ''
        assert response.status_code == status.HTTP_303_SEE_OTHER
        assert response['Location'] == 'http://example.com'

    def test_render_dict(self):
        factory = APIRequestFactory()

        class DummyView(APIView):
            renderer_classes = (AdminRenderer, )

            def get(self, request):
                return Response({'foo': 'a string'})
        view = DummyView.as_view()
        request = factory.get('/')
        response = view(request)
        response.render()
        self.assertContains(response, '<tr><th>Foo</th><td>a string</td></tr>', html=True)

    def test_render_dict_with_items_key(self):
        factory = APIRequestFactory()

        class DummyView(APIView):
            renderer_classes = (AdminRenderer, )

            def get(self, request):
                return Response({'items': 'a string'})

        view = DummyView.as_view()
        request = factory.get('/')
        response = view(request)
        response.render()
        self.assertContains(response, '<tr><th>Items</th><td>a string</td></tr>', html=True)

    def test_render_dict_with_iteritems_key(self):
        factory = APIRequestFactory()

        class DummyView(APIView):
            renderer_classes = (AdminRenderer, )

            def get(self, request):
                return Response({'iteritems': 'a string'})

        view = DummyView.as_view()
        request = factory.get('/')
        response = view(request)
        response.render()
        self.assertContains(response, '<tr><th>Iteritems</th><td>a string</td></tr>', html=True)

    def test_get_result_url(self):
        factory = APIRequestFactory()

        class DummyGenericViewsetLike(APIView):
            lookup_field = 'test'

            def get(self, request):
                response = Response()
                response.view = self
                return response

            def reverse_action(view, *args, **kwargs):
                self.assertEqual(kwargs['kwargs']['test'], 1)
                return '/example/'

        # get the view instance instead of the view function
        view = DummyGenericViewsetLike.as_view()
        request = factory.get('/')
        response = view(request)
        view = response.view

        self.assertEqual(self.renderer.get_result_url({'test': 1}, view), '/example/')
        self.assertIsNone(self.renderer.get_result_url({}, view))

    def test_get_result_url_no_result(self):
        factory = APIRequestFactory()

        class DummyView(APIView):
            lookup_field = 'test'

            def get(self, request):
                response = Response()
                response.view = self
                return response

        # get the view instance instead of the view function
        view = DummyView.as_view()
        request = factory.get('/')
        response = view(request)
        view = response.view

        self.assertIsNone(self.renderer.get_result_url({'test': 1}, view))
        self.assertIsNone(self.renderer.get_result_url({}, view))

    def test_get_context_result_urls(self):
        factory = APIRequestFactory()

        class DummyView(APIView):
            lookup_field = 'test'

            def reverse_action(view, url_name, args=None, kwargs=None):
                return '/%s/%d' % (url_name, kwargs['test'])

        # get the view instance instead of the view function
        view = DummyView.as_view()
        request = factory.get('/')
        response = view(request)

        data = [
            {'test': 1},
            {'url': '/example', 'test': 2},
            {'url': None, 'test': 3},
            {},
        ]
        context = {
            'view': DummyView(),
            'request': Request(request),
            'response': response
        }

        context = self.renderer.get_context(data, None, context)
        results = context['results']

        self.assertEqual(len(results), 4)
        self.assertEqual(results[0]['url'], '/detail/1')
        self.assertEqual(results[1]['url'], '/example')
        self.assertEqual(results[2]['url'], None)
        self.assertNotIn('url', results[3])


@pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
class TestDocumentationRenderer(TestCase):

    def test_document_with_link_named_data(self):
        """
        Ref #5395: Doc's `document.data` would fail with a Link named "data".
            As per #4972, use templatetag instead.
        """
        document = coreapi.Document(
            title='Data Endpoint API',
            url='https://api.example.org/',
            content={
                'data': coreapi.Link(
                    url='/data/',
                    action='get',
                    fields=[],
                    description='Return data.'
                )
            }
        )

        factory = APIRequestFactory()
        request = factory.get('/')

        renderer = DocumentationRenderer()

        html = renderer.render(document, accepted_media_type="text/html", renderer_context={"request": request})
        assert '<h1>Data Endpoint API</h1>' in html

    def test_shell_code_example_rendering(self):
        template = loader.get_template('rest_framework/docs/langs/shell.html')
        context = {
            'document': coreapi.Document(url='https://api.example.org/'),
            'link_key': 'testcases > list',
            'link': coreapi.Link(url='/data/', action='get', fields=[]),
        }
        html = template.render(context)
        assert 'testcases<span class="w"> </span>list' in html


@pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
class TestSchemaJSRenderer(TestCase):

    def test_schemajs_output(self):
        """
        Test output of the SchemaJS renderer as per #5608. Django 2.0 on Py3 prints binary data as b'xyz' in templates,
        and the base64 encoding used by SchemaJSRenderer outputs base64 as binary. Test fix.
        """
        factory = APIRequestFactory()
        request = factory.get('/')

        renderer = SchemaJSRenderer()

        output = renderer.render('data', renderer_context={"request": request})
        assert "'ImRhdGEi'" in output
        assert "'b'ImRhdGEi''" not in output
