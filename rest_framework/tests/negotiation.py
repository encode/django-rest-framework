from __future__ import unicode_literals
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.request import Request


factory = RequestFactory()


class MockJSONRenderer(object):
    media_type = 'application/json'


class MockHTMLRenderer(object):
    media_type = 'text/html'


class TestAcceptedMediaType(TestCase):
    def setUp(self):
        self.renderers = [MockJSONRenderer(), MockHTMLRenderer()]
        self.negotiator = DefaultContentNegotiation()

    def select_renderer(self, request):
        return self.negotiator.select_renderer(request, self.renderers)

    def test_client_without_accept_use_renderer(self):
        request = Request(factory.get('/'))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        self.assertEqual(accepted_media_type, 'application/json')

    def test_client_underspecifies_accept_use_renderer(self):
        request = Request(factory.get('/', HTTP_ACCEPT='*/*'))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        self.assertEqual(accepted_media_type, 'application/json')

    def test_client_overspecifies_accept_use_client(self):
        request = Request(factory.get('/', HTTP_ACCEPT='application/json; indent=8'))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        self.assertEqual(accepted_media_type, 'application/json; indent=8')
