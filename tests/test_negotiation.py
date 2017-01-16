from __future__ import unicode_literals

from django.test import TestCase

from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.renderers import BaseRenderer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.utils.mediatypes import _MediaType

factory = APIRequestFactory()


class MockOpenAPIRenderer(BaseRenderer):
    media_type = 'application/openapi+json;version=2.0'
    format = 'swagger'


class MockJSONRenderer(BaseRenderer):
    media_type = 'application/json'


class MockHTMLRenderer(BaseRenderer):
    media_type = 'text/html'


class NoCharsetSpecifiedRenderer(BaseRenderer):
    media_type = 'my/media'


class TestAcceptedMediaType(TestCase):
    def setUp(self):
        self.renderers = [MockJSONRenderer(), MockHTMLRenderer(), MockOpenAPIRenderer()]
        self.negotiator = DefaultContentNegotiation()

    def select_renderer(self, request):
        return self.negotiator.select_renderer(request, self.renderers)

    def test_client_without_accept_use_renderer(self):
        request = Request(factory.get('/'))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        assert accepted_media_type == 'application/json'

    def test_client_underspecifies_accept_use_renderer(self):
        request = Request(factory.get('/', HTTP_ACCEPT='*/*'))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        assert accepted_media_type == 'application/json'

    def test_client_overspecifies_accept_use_client(self):
        request = Request(factory.get('/', HTTP_ACCEPT='application/json; indent=8'))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        assert accepted_media_type == 'application/json; indent=8'

    def test_client_specifies_parameter(self):
        request = Request(factory.get('/', HTTP_ACCEPT='application/openapi+json;version=2.0'))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        assert accepted_media_type == 'application/openapi+json;version=2.0'
        assert accepted_renderer.format == 'swagger'

    def test_match_is_false_if_main_types_not_match(self):
        mediatype = _MediaType('test_1')
        anoter_mediatype = _MediaType('test_2')
        assert mediatype.match(anoter_mediatype) is False

    def test_mediatype_match_is_false_if_keys_not_match(self):
        mediatype = _MediaType(';test_param=foo')
        another_mediatype = _MediaType(';test_param=bar')
        assert mediatype.match(another_mediatype) is False

    def test_mediatype_precedence_with_wildcard_subtype(self):
        mediatype = _MediaType('test/*')
        assert mediatype.precedence == 1

    def test_mediatype_string_representation(self):
        mediatype = _MediaType('test/*; foo=bar')
        params_str = ''
        for key, val in mediatype.params.items():
            params_str += '; %s=%s' % (key, val)
        expected = 'test/*' + params_str
        assert str(mediatype) == expected
