from django.conf.urls.defaults import patterns, url
from django import http
from django.test import TestCase
from djangorestframework.compat import View
from djangorestframework.emitters import EmitterMixin, BaseEmitter
from djangorestframework.response import Response

DUMMYSTATUS = 200
DUMMYCONTENT = 'dummycontent'

EMITTER_A_SERIALIZER = lambda x: 'Emitter A: %s' % x
EMITTER_B_SERIALIZER = lambda x: 'Emitter B: %s' % x

class MockView(EmitterMixin, View):
    def get(self, request):
        response = Response(DUMMYSTATUS, DUMMYCONTENT)
        return self.emit(response)

class EmitterA(BaseEmitter):
    media_type = 'mock/emittera'

    def emit(self, output, verbose=False):
        return EMITTER_A_SERIALIZER(output)

class EmitterB(BaseEmitter):
    media_type = 'mock/emitterb'

    def emit(self, output, verbose=False):
        return EMITTER_B_SERIALIZER(output)


urlpatterns = patterns('',
    url(r'^$', MockView.as_view(emitters=[EmitterA, EmitterB])),
)


class EmitterIntegrationTests(TestCase):
    """End-to-end testing of emitters using an EmitterMixin on a generic view."""

    urls = 'djangorestframework.tests.emitters'

    def test_default_emitter_serializes_content(self):
        """If the Accept header is not set the default emitter should serialize the response."""
        resp = self.client.get('/')
        self.assertEquals(resp['Content-Type'], EmitterA.media_type)
        self.assertEquals(resp.content, EMITTER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_default_emitter_serializes_content_on_accept_any(self):
        """If the Accept header is set to */* the default emitter should serialize the response."""
        resp = self.client.get('/', HTTP_ACCEPT='*/*')
        self.assertEquals(resp['Content-Type'], EmitterA.media_type)
        self.assertEquals(resp.content, EMITTER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_specified_emitter_serializes_content_default_case(self):
        """If the Accept header is set the specified emitter should serialize the response.
        (In this case we check that works for the default emitter)"""
        resp = self.client.get('/', HTTP_ACCEPT=EmitterA.media_type)
        self.assertEquals(resp['Content-Type'], EmitterA.media_type)
        self.assertEquals(resp.content, EMITTER_A_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)

    def test_specified_emitter_serializes_content_non_default_case(self):
        """If the Accept header is set the specified emitter should serialize the response.
        (In this case we check that works for a non-default emitter)"""
        resp = self.client.get('/', HTTP_ACCEPT=EmitterB.media_type)
        self.assertEquals(resp['Content-Type'], EmitterB.media_type)
        self.assertEquals(resp.content, EMITTER_B_SERIALIZER(DUMMYCONTENT))
        self.assertEquals(resp.status_code, DUMMYSTATUS)
    
    def test_unsatisfiable_accept_header_on_request_returns_406_status(self):
        """If the Accept header is unsatisfiable we should return a 406 Not Acceptable response."""
        resp = self.client.get('/', HTTP_ACCEPT='foo/bar')
        self.assertEquals(resp.status_code, 406)