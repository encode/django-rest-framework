from unittest import mock

import pytest
from django.http import Http404
from django.test import TestCase

from rest_framework import exceptions
from rest_framework.negotiation import (
    BaseContentNegotiation, DefaultContentNegotiation
)
from rest_framework.renderers import BaseRenderer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework.utils import mediatypes
from rest_framework.utils.mediatypes import (
    _MediaType, order_parsed_by_precedence
)

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
        another_mediatype = _MediaType('test_2')
        assert mediatype.match(another_mediatype) is False

    def test_mediatype_match_is_false_if_keys_not_match(self):
        mediatype = _MediaType(';test_param=foo')
        another_mediatype = _MediaType(';test_param=bar')
        assert mediatype.match(another_mediatype) is False

    def test_mediatype_precedence_with_wildcard_subtype(self):
        mediatype = _MediaType('test/*')
        assert mediatype.precedence == 1

    def test_mediatype_string_representation(self):
        mediatype = _MediaType('test/*; foo=bar')
        assert str(mediatype) == 'test/*; foo=bar'

    def test_raise_error_if_no_suitable_renderers_found(self):
        class MockRenderer:
            format = 'xml'
        renderers = [MockRenderer()]
        with pytest.raises(Http404):
            self.negotiator.filter_renderers(renderers, format='json')

    def test_accept_header_length_limit(self):
        prefix = 'text/plain,'
        limit = self.negotiator.max_accept_header_length
        header = prefix + ' ' * (limit - len(prefix) - len('application/json')) + 'application/json'
        request = Request(factory.get('/', HTTP_ACCEPT=header))
        assert self.negotiator.get_accept_list(request) == ['text/plain', 'application/json']

        request = Request(factory.get('/', HTTP_ACCEPT=header + 'x'))
        assert self.negotiator.get_accept_list(request) == ['text/plain']

    def test_accept_header_without_separator(self):
        header = 'x' * (self.negotiator.max_accept_header_length + 1)
        request = Request(factory.get('/', HTTP_ACCEPT=header))
        assert self.negotiator.get_accept_list(request) == []
        with pytest.raises(exceptions.NotAcceptable):
            self.select_renderer(request)

    def test_accept_token_length_limit(self):
        prefix = 'application/json; padding='
        token = prefix + 'x' * (self.negotiator.max_media_type_length - len(prefix))
        request = Request(factory.get('/', HTTP_ACCEPT=token))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        assert accepted_renderer is self.renderers[0]
        assert accepted_media_type == token

        request = Request(factory.get('/', HTTP_ACCEPT=token + 'x, text/html'))
        assert self.negotiator.get_accept_list(request) == ['text/html']
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        assert accepted_renderer is self.renderers[1]
        assert accepted_media_type == 'text/html'

    def test_accept_token_count_limit(self):
        tokens = ['text/x%d' % i for i in range(self.negotiator.max_accept_tokens - 1)]
        request = Request(factory.get('/', HTTP_ACCEPT=', '.join(tokens + ['application/json'])))
        accepted_renderer, accepted_media_type = self.select_renderer(request)
        assert accepted_renderer is self.renderers[0]
        assert accepted_media_type == 'application/json'

        request = Request(factory.get('/', HTTP_ACCEPT=', '.join(tokens + ['text/plain', 'application/json'])))
        with pytest.raises(exceptions.NotAcceptable):
            self.select_renderer(request)

    def test_media_type_parse_error(self):
        with mock.patch.object(
            mediatypes, 'parse_header_parameters', side_effect=ValueError
        ) as parse:
            media_type = _MediaType('application/json')
        parse.assert_called_once_with('application/json')
        assert media_type.full_type == ''
        assert media_type.params == {}

    def test_media_type_equality(self):
        one = _MediaType('application/json')
        same = _MediaType('application/json')
        assert one == same
        assert hash(one) == hash(same)
        assert one != _MediaType('text/html')
        assert one != _MediaType('application/json; indent=4')

    def test_parsed_media_type_precedence(self):
        wildcard = _MediaType('*/*')
        subtype = _MediaType('application/*')
        json = _MediaType('application/json')
        parameterized = _MediaType('application/json; indent=4')
        buckets = order_parsed_by_precedence([
            wildcard, json, subtype, parameterized, _MediaType('application/json'),
        ])
        assert buckets == [{parameterized}, {json}, {subtype}, {wildcard}]

    def test_accept_tokens_cached_on_request(self):
        token = 'application/json; indent=8'
        request = Request(factory.get('/', HTTP_ACCEPT=token))
        with mock.patch.object(
            mediatypes, 'parse_header_parameters',
            wraps=mediatypes.parse_header_parameters
        ) as parse:
            for _ in range(2):
                self.select_renderer(request)
            assert parse.call_args_list.count(mock.call(token)) == 1

            request = Request(factory.get('/', HTTP_ACCEPT=token))
            self.select_renderer(request)
            assert parse.call_args_list.count(mock.call(token)) == 2


class BaseContentNegotiationTests(TestCase):

    def setUp(self):
        self.negotiator = BaseContentNegotiation()

    def test_raise_error_for_abstract_select_parser_method(self):
        with pytest.raises(NotImplementedError):
            self.negotiator.select_parser(None, None)

    def test_raise_error_for_abstract_select_renderer_method(self):
        with pytest.raises(NotImplementedError):
            self.negotiator.select_renderer(None, None)
