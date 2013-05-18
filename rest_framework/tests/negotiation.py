from __future__ import unicode_literals
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.request import Request
from rest_framework.renderers import BaseRenderer


factory = RequestFactory()


class MockJSONRenderer(BaseRenderer):
    media_type = 'application/json'

class MockHTMLRenderer(BaseRenderer):
    media_type = 'text/html'

class NoCharsetSpecifiedRenderer(BaseRenderer):
    media_type = 'my/media'

class CharsetSpecifiedRenderer(BaseRenderer):
    media_type = 'my/media'
    charset = 'mycharset'

class TestAcceptedMediaType(TestCase):
    def setUp(self):
        self.renderers = [MockJSONRenderer(), MockHTMLRenderer()]
        self.negotiator = DefaultContentNegotiation()

    def select_renderer(self, request):
        return self.negotiator.select_renderer(request, self.renderers)

    def test_client_without_accept_use_renderer(self):
        request = Request(factory.get('/'))
        accepted_renderer, accepted_media_type, charset = self.select_renderer(request)
        self.assertEqual(accepted_media_type, 'application/json')

    def test_client_underspecifies_accept_use_renderer(self):
        request = Request(factory.get('/', HTTP_ACCEPT='*/*'))
        accepted_renderer, accepted_media_type, charset = self.select_renderer(request)
        self.assertEqual(accepted_media_type, 'application/json')

    def test_client_overspecifies_accept_use_client(self):
        request = Request(factory.get('/', HTTP_ACCEPT='application/json; indent=8'))
        accepted_renderer, accepted_media_type, charset = self.select_renderer(request)
        self.assertEqual(accepted_media_type, 'application/json; indent=8')
        
class TestCharset(TestCase):
    def setUp(self):
        self.renderers = [NoCharsetSpecifiedRenderer()]
        self.negotiator = DefaultContentNegotiation()
    
    def test_returns_none_if_no_charset_set(self):
        request = Request(factory.get('/'))
        renderers = [NoCharsetSpecifiedRenderer()]
        _, _, charset = self.negotiator.select_renderer(request, renderers)
        self.assertIsNone(charset)
    
    def test_returns_attribute_from_renderer_if_charset_is_set(self):
        request = Request(factory.get('/'))
        renderers = [CharsetSpecifiedRenderer()]
        _, _, charset =  self.negotiator.select_renderer(request, renderers)
        self.assertEquals(CharsetSpecifiedRenderer.charset, charset)