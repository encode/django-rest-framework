import json
import unittest

from django.conf.urls.defaults import patterns, url, include
from django.test import TestCase

from djangorestframework.response import Response, ImmediateResponse
from djangorestframework.views import View
from djangorestframework.compat import RequestFactory
from djangorestframework import status
from djangorestframework.renderers import (
    BaseRenderer,
    JSONRenderer,
    DocumentingHTMLRenderer,
    DEFAULT_RENDERERS
)


class TestResponseDetermineRenderer(TestCase):

    def get_response(self, url='', accept_list=[], renderers=[]):
        kwargs = {}
        if accept_list is not None:
            kwargs['HTTP_ACCEPT'] = ','.join(accept_list)
        request = RequestFactory().get(url, **kwargs)
        return Response(request=request, renderers=renderers)

    def get_renderer_mock(self, media_type):
        return type('RendererMock', (BaseRenderer,), {
            'media_type': media_type,
        })()

    def test_determine_accept_list_accept_header(self):
        """
        Test that determine_accept_list takes the Accept header.
        """
        accept_list = ['application/pickle', 'application/json']
        response = self.get_response(accept_list=accept_list)
        self.assertEqual(response._determine_accept_list(), accept_list)

    def test_determine_accept_list_default(self):
        """
        Test that determine_accept_list takes the default renderer if Accept is not specified.
        """
        response = self.get_response(accept_list=None)
        self.assertEqual(response._determine_accept_list(), ['*/*'])

    def test_determine_accept_list_overriden_header(self):
        """
        Test Accept header overriding.
        """
        accept_list = ['application/pickle', 'application/json']
        response = self.get_response(url='?_accept=application/x-www-form-urlencoded',
            accept_list=accept_list)
        self.assertEqual(response._determine_accept_list(), ['application/x-www-form-urlencoded'])

    def test_determine_renderer(self):
        """
        Test that right renderer is chosen, in the order of Accept list.
        """
        accept_list = ['application/pickle', 'application/json']
        prenderer = self.get_renderer_mock('application/pickle')
        jrenderer = self.get_renderer_mock('application/json')

        response = self.get_response(accept_list=accept_list, renderers=(prenderer, jrenderer))
        renderer, media_type = response._determine_renderer()
        self.assertEqual(media_type, 'application/pickle')
        self.assertTrue(renderer, prenderer)

        response = self.get_response(accept_list=accept_list, renderers=(jrenderer,))
        renderer, media_type = response._determine_renderer()
        self.assertEqual(media_type, 'application/json')
        self.assertTrue(renderer, jrenderer)

    def test_determine_renderer_default(self):
        """
        Test determine renderer when Accept was not specified.
        """
        prenderer = self.get_renderer_mock('application/pickle')

        response = self.get_response(accept_list=None, renderers=(prenderer,))
        renderer, media_type = response._determine_renderer()
        self.assertEqual(media_type, '*/*')
        self.assertTrue(renderer, prenderer)

    def test_determine_renderer_no_renderer(self):
        """
        Test determine renderer when no renderer can satisfy the Accept list.
        """
        accept_list = ['application/json']
        prenderer = self.get_renderer_mock('application/pickle')

        response = self.get_response(accept_list=accept_list, renderers=(prenderer,))
        self.assertRaises(ImmediateResponse, response._determine_renderer)


class TestResponseRenderContent(TestCase):

    def get_response(self, url='', accept_list=[], content=None):
        request = RequestFactory().get(url, HTTP_ACCEPT=','.join(accept_list))
        return Response(request=request, content=content, renderers=[r() for r in DEFAULT_RENDERERS])

    def test_render(self):
        """
        Test rendering simple data to json.
        """
        content = {'a': 1, 'b': [1, 2, 3]}
        content_type = 'application/json'
        response = self.get_response(accept_list=[content_type], content=content)
        response.render()
        self.assertEqual(json.loads(response.content), content)
        self.assertEqual(response['Content-Type'], content_type)


DUMMYSTATUS = status.HTTP_200_OK
DUMMYCONTENT = 'dummycontent'

RENDERER_A_SERIALIZER = lambda x: 'Renderer A: %s' % x
RENDERER_B_SERIALIZER = lambda x: 'Renderer B: %s' % x


class RendererA(BaseRenderer):
    media_type = 'mock/renderera'
    format = "formata"

    def render(self, obj=None, media_type=None):
        return RENDERER_A_SERIALIZER(obj)


class RendererB(BaseRenderer):
    media_type = 'mock/rendererb'
    format = "formatb"

    def render(self, obj=None, media_type=None):
        return RENDERER_B_SERIALIZER(obj)


class MockView(View):
    renderers = (RendererA, RendererB)

    def get(self, request, **kwargs):
        return Response(DUMMYCONTENT, status=DUMMYSTATUS)


class HTMLView(View):
    renderers = (DocumentingHTMLRenderer, )

    def get(self, request, **kwargs):
        return Response('text')


class HTMLView1(View):
    renderers = (DocumentingHTMLRenderer, JSONRenderer)

    def get(self, request, **kwargs):
        return Response('text')


urlpatterns = patterns('',
    url(r'^.*\.(?P<format>.+)$', MockView.as_view(renderers=[RendererA, RendererB])),
    url(r'^$', MockView.as_view(renderers=[RendererA, RendererB])),
    url(r'^html$', HTMLView.as_view()),
    url(r'^html1$', HTMLView1.as_view()),
    url(r'^restframework', include('djangorestframework.urls', namespace='djangorestframework'))
)


# TODO: Clean tests bellow - remove duplicates with above, better unit testing, ...
class RendererIntegrationTests(TestCase):
    """
    End-to-end testing of renderers using an ResponseMixin on a generic view.
    """

    urls = 'djangorestframework.tests.response'

    def test_default_renderer_serializes_content(self):
        """If the Accept header is not set the default renderer should serialize the response."""
        resp = self.client.get('/')
        self.assertEquals(resp['Content-Type'], RendererA.media_type)
        self.assertEquals(resp.content, RENDERER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_head_method_serializes_no_content(self):
        """No response must be included in HEAD requests."""
        resp = self.client.head('/')
        self.assertEquals(resp.status_code, DUMMYSTATUS)
        self.assertEquals(resp['Content-Type'], RendererA.media_type)
        self.assertEquals(resp.content, '')

    def test_default_renderer_serializes_content_on_accept_any(self):
        """If the Accept header is set to */* the default renderer should serialize the response."""
        resp = self.client.get('/', HTTP_ACCEPT='*/*')
        self.assertEquals(resp['Content-Type'], RendererA.media_type)
        self.assertEquals(resp.content, RENDERER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_serializes_content_default_case(self):
        """If the Accept header is set the specified renderer should serialize the response.
        (In this case we check that works for the default renderer)"""
        resp = self.client.get('/', HTTP_ACCEPT=RendererA.media_type)
        self.assertEquals(resp['Content-Type'], RendererA.media_type)
        self.assertEquals(resp.content, RENDERER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_serializes_content_non_default_case(self):
        """If the Accept header is set the specified renderer should serialize the response.
        (In this case we check that works for a non-default renderer)"""
        resp = self.client.get('/', HTTP_ACCEPT=RendererB.media_type)
        self.assertEquals(resp['Content-Type'], RendererB.media_type)
        self.assertEquals(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_serializes_content_on_accept_query(self):
        """The '_accept' query string should behave in the same way as the Accept header."""
        resp = self.client.get('/?_accept=%s' % RendererB.media_type)
        self.assertEquals(resp['Content-Type'], RendererB.media_type)
        self.assertEquals(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    @unittest.skip('can\'t pass because view is a simple Django view and response is an ImmediateResponse')
    def test_unsatisfiable_accept_header_on_request_returns_406_status(self):
        """If the Accept header is unsatisfiable we should return a 406 Not Acceptable response."""
        resp = self.client.get('/', HTTP_ACCEPT='foo/bar')
        self.assertEquals(resp.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_specified_renderer_serializes_content_on_format_query(self):
        """If a 'format' query is specified, the renderer with the matching
        format attribute should serialize the response."""
        resp = self.client.get('/?format=%s' % RendererB.format)
        self.assertEquals(resp['Content-Type'], RendererB.media_type)
        self.assertEquals(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_serializes_content_on_format_kwargs(self):
        """If a 'format' keyword arg is specified, the renderer with the matching
        format attribute should serialize the response."""
        resp = self.client.get('/something.formatb')
        self.assertEquals(resp['Content-Type'], RendererB.media_type)
        self.assertEquals(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_specified_renderer_is_used_on_format_query_with_matching_accept(self):
        """If both a 'format' query and a matching Accept header specified,
        the renderer with the matching format attribute should serialize the response."""
        resp = self.client.get('/?format=%s' % RendererB.format,
                               HTTP_ACCEPT=RendererB.media_type)
        self.assertEquals(resp['Content-Type'], RendererB.media_type)
        self.assertEquals(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_conflicting_format_query_and_accept_ignores_accept(self):
        """If a 'format' query is specified that does not match the Accept
        header, we should only honor the 'format' query string."""
        resp = self.client.get('/?format=%s' % RendererB.format,
                               HTTP_ACCEPT='dummy')
        self.assertEquals(resp['Content-Type'], RendererB.media_type)
        self.assertEquals(resp.content, RENDERER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)


class Issue122Tests(TestCase):
    """
    Tests that covers #122.
    """
    urls = 'djangorestframework.tests.response'

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
