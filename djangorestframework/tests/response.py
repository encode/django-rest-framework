import json

from django.conf.urls.defaults import patterns, url
from django.test import TestCase

from djangorestframework.response import Response, ErrorResponse
from djangorestframework.mixins import ResponseMixin
from djangorestframework.views import View
from djangorestframework.compat import View as DjangoView
from djangorestframework.renderers import BaseRenderer, DEFAULT_RENDERERS
from djangorestframework.compat import RequestFactory
from djangorestframework import status
from djangorestframework.renderers import BaseRenderer, JSONRenderer, YAMLRenderer, \
    XMLRenderer, JSONPRenderer, DocumentingHTMLRenderer


class TestResponseDetermineRenderer(TestCase):

    def get_response(self, url='', accept_list=[], renderers=[]):
        request = RequestFactory().get(url, HTTP_ACCEPT=','.join(accept_list))
        return Response(request=request, renderers=renderers)

    def get_renderer_mock(self, media_type):
        return type('RendererMock', (BaseRenderer,), {
            'media_type': media_type,
        })

    def test_determine_accept_list_accept_header(self):
        """
        Test that determine_accept_list takes the Accept header.
        """
        accept_list = ['application/pickle', 'application/json']
        response = self.get_response(accept_list=accept_list)
        self.assertEqual(response._determine_accept_list(), accept_list)
        
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
        PRenderer = self.get_renderer_mock('application/pickle')
        JRenderer = self.get_renderer_mock('application/json')

        renderers = (PRenderer, JRenderer)
        response = self.get_response(accept_list=accept_list, renderers=renderers)
        renderer, media_type = response._determine_renderer()
        self.assertEqual(media_type, 'application/pickle')
        self.assertTrue(isinstance(renderer, PRenderer))

        renderers = (JRenderer,)
        response = self.get_response(accept_list=accept_list, renderers=renderers)
        renderer, media_type = response._determine_renderer()
        self.assertEqual(media_type, 'application/json')
        self.assertTrue(isinstance(renderer, JRenderer))
        
    def test_determine_renderer_no_renderer(self):
        """
        Test determine renderer when no renderer can satisfy the Accept list.
        """
        accept_list = ['application/json']
        PRenderer = self.get_renderer_mock('application/pickle')

        renderers = (PRenderer,)
        response = self.get_response(accept_list=accept_list, renderers=renderers)
        self.assertRaises(ErrorResponse, response._determine_renderer)


class TestResponseRenderContent(TestCase):
    
    def get_response(self, url='', accept_list=[], content=None):
        request = RequestFactory().get(url, HTTP_ACCEPT=','.join(accept_list))
        return Response(request=request, content=content, renderers=DEFAULT_RENDERERS)

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


class MockView(ResponseMixin, DjangoView):
    renderers = (RendererA, RendererB)

    def get(self, request, **kwargs):
        response = Response(DUMMYCONTENT, status=DUMMYSTATUS)
        return self.prepare_response(response)


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

# TODO: can't pass because view is a simple Django view and response is an ErrorResponse
#    def test_unsatisfiable_accept_header_on_request_returns_406_status(self):
#        """If the Accept header is unsatisfiable we should return a 406 Not Acceptable response."""
#        resp = self.client.get('/', HTTP_ACCEPT='foo/bar')
#        self.assertEquals(resp.status_code, status.HTTP_406_NOT_ACCEPTABLE)

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

    def test_bla(self):
        resp = self.client.get('/?format=formatb',
            HTTP_ACCEPT='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8')
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
        resp = self.client.get('/html')
        
    def test_html_renderer_is_first(self):
        """
        Test if no infinite recursion occurs.
        """
        resp = self.client.get('/html1')
