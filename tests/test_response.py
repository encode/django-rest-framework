from django.test import TestCase, override_settings
from django.urls import include, path, re_path

from rest_framework import generics, routers, serializers, status, viewsets
from rest_framework.parsers import JSONParser
from rest_framework.renderers import (
    BaseRenderer, BrowsableAPIRenderer, JSONRenderer
)
from rest_framework.response import Response
from rest_framework.views import APIView
from tests.models import BasicModel


# Serializer used to test BasicModel
class BasicModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = BasicModel
        fields = '__all__'


class MockPickleRenderer(BaseRenderer):
    media_type = 'application/pickle'


class MockJsonRenderer(BaseRenderer):
    media_type = 'application/json'


class MockTextMediaRenderer(BaseRenderer):
    media_type = 'text/html'


DUMMYSTATUS = status.HTTP_200_OK
DUMMYCONTENT = 'dummycontent'


def RENDERER_A_SERIALIZER(x):
    return ('Renderer A: %s' % x).encode('ascii')


def RENDERER_B_SERIALIZER(x):
    return ('Renderer B: %s' % x).encode('ascii')


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


class RendererC(RendererB):
    media_type = 'mock/rendererc'
    format = 'formatc'
    charset = "rendererc"


class MockView(APIView):
    renderer_classes = (RendererA, RendererB, RendererC)

    def get(self, request, **kwargs):
        return Response(DUMMYCONTENT, status=DUMMYSTATUS)


class MockViewSettingContentType(APIView):
    renderer_classes = (RendererA, RendererB, RendererC)

    def get(self, request, **kwargs):
        return Response(DUMMYCONTENT, status=DUMMYSTATUS, content_type='setbyview')


class JSONView(APIView):
    parser_classes = (JSONParser,)

    def post(self, request, **kwargs):
        assert request.data
        return Response(DUMMYCONTENT)


class HTMLView(APIView):
    renderer_classes = (BrowsableAPIRenderer, )

    def get(self, request, **kwargs):
        return Response('text')


class HTMLView1(APIView):
    renderer_classes = (BrowsableAPIRenderer, JSONRenderer)

    def get(self, request, **kwargs):
        return Response('text')


class HTMLNewModelViewSet(viewsets.ModelViewSet):
    serializer_class = BasicModelSerializer
    queryset = BasicModel.objects.all()


class HTMLNewModelView(generics.ListCreateAPIView):
    renderer_classes = (BrowsableAPIRenderer,)
    permission_classes = []
    serializer_class = BasicModelSerializer
    queryset = BasicModel.objects.all()


new_model_viewset_router = routers.DefaultRouter()
new_model_viewset_router.register(r'', HTMLNewModelViewSet)


urlpatterns = [
    path('setbyview', MockViewSettingContentType.as_view(renderer_classes=[RendererA, RendererB, RendererC])),
    re_path(r'^.*\.(?P<format>.+)$', MockView.as_view(renderer_classes=[RendererA, RendererB, RendererC])),
    path('', MockView.as_view(renderer_classes=[RendererA, RendererB, RendererC])),
    path('html', HTMLView.as_view()),
    path('json', JSONView.as_view()),
    path('html1', HTMLView1.as_view()),
    path('html_new_model', HTMLNewModelView.as_view()),
    path('html_new_model_viewset', include(new_model_viewset_router.urls)),
    path('restframework', include('rest_framework.urls', namespace='rest_framework'))
]


# TODO: Clean tests bellow - remove duplicates with above, better unit testing, ...
@override_settings(ROOT_URLCONF='tests.test_response')
class RendererIntegrationTests(TestCase):
    """
    End-to-end testing of renderers using an ResponseMixin on a generic view.
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

    def test_specified_renderer_serializes_content_on_format_query(self):
        """If a 'format' query is specified, the renderer with the matching
        format attribute should serialize the response."""
        resp = self.client.get('/?format=%s' % RendererB.format)
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
        resp = self.client.get('/?format=%s' % RendererB.format,
                               HTTP_ACCEPT=RendererB.media_type)
        self.assertEqual(resp['Content-Type'], RendererB.media_type + '; charset=utf-8')
        self.assertEqual(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEqual(resp.status_code, DUMMYSTATUS)


@override_settings(ROOT_URLCONF='tests.test_response')
class UnsupportedMediaTypeTests(TestCase):
    def test_should_allow_posting_json(self):
        response = self.client.post('/json', data='{"test": 123}', content_type='application/json')

        self.assertEqual(response.status_code, 200)

    def test_should_not_allow_posting_xml(self):
        response = self.client.post('/json', data='<test>123</test>', content_type='application/xml')

        self.assertEqual(response.status_code, 415)

    def test_should_not_allow_posting_a_form(self):
        response = self.client.post('/json', data={'test': 123})

        self.assertEqual(response.status_code, 415)


@override_settings(ROOT_URLCONF='tests.test_response')
class Issue122Tests(TestCase):
    """
    Tests that covers #122.
    """
    def test_only_html_renderer(self):
        """
        Test if no infinite recursion occurs.
        """
        self.client.get('/html')

    def test_html_renderer_is_first(self):
        """
        Test if no infinite recursion occurs.
        """
        self.client.get('/html1')


@override_settings(ROOT_URLCONF='tests.test_response')
class Issue467Tests(TestCase):
    """
    Tests for #467
    """
    def test_form_has_label_and_help_text(self):
        resp = self.client.get('/html_new_model')
        self.assertEqual(resp['Content-Type'], 'text/html; charset=utf-8')
        # self.assertContains(resp, 'Text comes here')
        # self.assertContains(resp, 'Text description.')


@override_settings(ROOT_URLCONF='tests.test_response')
class Issue807Tests(TestCase):
    """
    Covers #807
    """
    def test_does_not_append_charset_by_default(self):
        """
        Renderers don't include a charset unless set explicitly.
        """
        headers = {"HTTP_ACCEPT": RendererA.media_type}
        resp = self.client.get('/', **headers)
        expected = "{}; charset={}".format(RendererA.media_type, 'utf-8')
        self.assertEqual(expected, resp['Content-Type'])

    def test_if_there_is_charset_specified_on_renderer_it_gets_appended(self):
        """
        If renderer class has charset attribute declared, it gets appended
        to Response's Content-Type
        """
        headers = {"HTTP_ACCEPT": RendererC.media_type}
        resp = self.client.get('/', **headers)
        expected = "{}; charset={}".format(RendererC.media_type, RendererC.charset)
        self.assertEqual(expected, resp['Content-Type'])

    def test_content_type_set_explicitly_on_response(self):
        """
        The content type may be set explicitly on the response.
        """
        headers = {"HTTP_ACCEPT": RendererC.media_type}
        resp = self.client.get('/setbyview', **headers)
        self.assertEqual('setbyview', resp['Content-Type'])

    def test_form_has_label_and_help_text(self):
        resp = self.client.get('/html_new_model')
        self.assertEqual(resp['Content-Type'], 'text/html; charset=utf-8')
        # self.assertContains(resp, 'Text comes here')
        # self.assertContains(resp, 'Text description.')
