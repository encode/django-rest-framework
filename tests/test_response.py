from __future__ import unicode_literals
from django.conf.urls import patterns, url, include
from django.test import TestCase
from django.utils import six
from tests.models import BasicModel, BasicModelSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics
from rest_framework import routers
from rest_framework import status
from rest_framework.renderers import (
    BaseRenderer,
    JSONRenderer,
    BrowsableAPIRenderer
)
from rest_framework import viewsets
from rest_framework.settings import api_settings


class MockPickleRenderer(BaseRenderer):
    media_type = 'application/pickle'


class MockJsonRenderer(BaseRenderer):
    media_type = 'application/json'


class MockTextMediaRenderer(BaseRenderer):
    media_type = 'text/html'

DUMMYSTATUS = status.HTTP_200_OK
DUMMYCONTENT = 'dummycontent'

RENDERER_A_SERIALIZER = lambda x: ('Renderer A: %s' % x).encode('ascii')
RENDERER_B_SERIALIZER = lambda x: ('Renderer B: %s' % x).encode('ascii')


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


class HTMLView(APIView):
    renderer_classes = (BrowsableAPIRenderer, )

    def get(self, request, **kwargs):
        return Response('text')


class HTMLView1(APIView):
    renderer_classes = (BrowsableAPIRenderer, JSONRenderer)

    def get(self, request, **kwargs):
        return Response('text')


class HTMLNewModelViewSet(viewsets.ModelViewSet):
    model = BasicModel


class HTMLNewModelView(generics.ListCreateAPIView):
    renderer_classes = (BrowsableAPIRenderer,)
    permission_classes = []
    serializer_class = BasicModelSerializer
    model = BasicModel


new_model_viewset_router = routers.DefaultRouter()
new_model_viewset_router.register(r'', HTMLNewModelViewSet)


urlpatterns = patterns(
    '',
    url(r'^setbyview$', MockViewSettingContentType.as_view(renderer_classes=[RendererA, RendererB, RendererC])),
    url(r'^.*\.(?P<format>.+)$', MockView.as_view(renderer_classes=[RendererA, RendererB, RendererC])),
    url(r'^$', MockView.as_view(renderer_classes=[RendererA, RendererB, RendererC])),
    url(r'^html$', HTMLView.as_view()),
    url(r'^html1$', HTMLView1.as_view()),
    url(r'^html_new_model$', HTMLNewModelView.as_view()),
    url(r'^html_new_model_viewset', include(new_model_viewset_router.urls)),
    url(r'^restframework', include('rest_framework.urls', namespace='rest_framework'))
)


# TODO: Clean tests bellow - remove duplicates with above, better unit testing, ...
class RendererIntegrationTests(TestCase):
    """
    End-to-end testing of renderers using an ResponseMixin on a generic view.
    """

    urls = 'tests.test_response'

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
        self.assertEqual(resp.content, six.b(''))

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

    def test_specified_renderer_serializes_content_on_accept_query(self):
        """The '_accept' query string should behave in the same way as the Accept header."""
        param = '?%s=%s' % (
            api_settings.URL_ACCEPT_OVERRIDE,
            RendererB.media_type
        )
        resp = self.client.get('/' + param)
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


class Issue122Tests(TestCase):
    """
    Tests that covers #122.
    """
    urls = 'tests.test_response'

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


class Issue467Tests(TestCase):
    """
    Tests for #467
    """

    urls = 'tests.test_response'

    def test_form_has_label_and_help_text(self):
        resp = self.client.get('/html_new_model')
        self.assertEqual(resp['Content-Type'], 'text/html; charset=utf-8')
        self.assertContains(resp, 'Text comes here')
        self.assertContains(resp, 'Text description.')


class Issue807Tests(TestCase):
    """
    Covers #807
    """

    urls = 'tests.test_response'

    def test_does_not_append_charset_by_default(self):
        """
        Renderers don't include a charset unless set explicitly.
        """
        headers = {"HTTP_ACCEPT": RendererA.media_type}
        resp = self.client.get('/', **headers)
        expected = "{0}; charset={1}".format(RendererA.media_type, 'utf-8')
        self.assertEqual(expected, resp['Content-Type'])

    def test_if_there_is_charset_specified_on_renderer_it_gets_appended(self):
        """
        If renderer class has charset attribute declared, it gets appended
        to Response's Content-Type
        """
        headers = {"HTTP_ACCEPT": RendererC.media_type}
        resp = self.client.get('/', **headers)
        expected = "{0}; charset={1}".format(RendererC.media_type, RendererC.charset)
        self.assertEqual(expected, resp['Content-Type'])

    def test_content_type_set_explictly_on_response(self):
        """
        The content type may be set explictly on the response.
        """
        headers = {"HTTP_ACCEPT": RendererC.media_type}
        resp = self.client.get('/setbyview', **headers)
        self.assertEqual('setbyview', resp['Content-Type'])

    def test_viewset_label_help_text(self):
        param = '?%s=%s' % (
            api_settings.URL_ACCEPT_OVERRIDE,
            'text/html'
        )
        resp = self.client.get('/html_new_model_viewset/' + param)
        self.assertEqual(resp['Content-Type'], 'text/html; charset=utf-8')
        self.assertContains(resp, 'Text comes here')
        self.assertContains(resp, 'Text description.')

    def test_form_has_label_and_help_text(self):
        resp = self.client.get('/html_new_model')
        self.assertEqual(resp['Content-Type'], 'text/html; charset=utf-8')
        self.assertContains(resp, 'Text comes here')
        self.assertContains(resp, 'Text description.')
