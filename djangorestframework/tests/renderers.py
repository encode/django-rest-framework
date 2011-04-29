from django.conf.urls.defaults import patterns, url
from django import http
from django.test import TestCase
from djangorestframework.compat import View
from djangorestframework.renderers import BaseRenderer
from djangorestframework.mixins import ResponseMixin
from djangorestframework.response import Response

DUMMYSTATUS = 200
DUMMYCONTENT = 'dummycontent'

RENDERER_A_SERIALIZER = lambda x: 'Renderer A: %s' % x
RENDERER_B_SERIALIZER = lambda x: 'Renderer B: %s' % x

class MockView(ResponseMixin, View):
    def get(self, request):
        response = Response(DUMMYSTATUS, DUMMYCONTENT)
        return self.render(response)

class RendererA(BaseRenderer):
    media_type = 'mock/renderera'

    def render(self, output, verbose=False):
        return RENDERER_A_SERIALIZER(output)

class RendererB(BaseRenderer):
    media_type = 'mock/rendererb'

    def render(self, output, verbose=False):
        return RENDERER_B_SERIALIZER(output)


urlpatterns = patterns('',
    url(r'^$', MockView.as_view(renderers=[RendererA, RendererB])),
)


class RendererIntegrationTests(TestCase):
    """End-to-end testing of renderers using an RendererMixin on a generic view."""

    urls = 'djangorestframework.tests.renderers'

    def test_default_renderer_serializes_content(self):
        """If the Accept header is not set the default renderer should serialize the response."""
        resp = self.client.get('/')
        self.assertEquals(resp['Content-Type'], RendererA.media_type)
        self.assertEquals(resp.content, RENDERER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

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
    
    def test_unsatisfiable_accept_header_on_request_returns_406_status(self):
        """If the Accept header is unsatisfiable we should return a 406 Not Acceptable response."""
        resp = self.client.get('/', HTTP_ACCEPT='foo/bar')
        self.assertEquals(resp.status_code, 406)