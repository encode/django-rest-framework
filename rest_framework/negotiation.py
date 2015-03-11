"""
Content negotiation deals with selecting an appropriate renderer given the
incoming request.  Typically this will be based on the request's Accept header.
"""
from __future__ import unicode_literals
from django.http import Http404
from rest_framework import exceptions
from rest_framework.settings import api_settings
from rest_framework.utils.mediatypes import order_by_precedence, media_type_matches
from rest_framework.utils.mediatypes import _MediaType


class BaseContentNegotiation(object):
    def select_parser(self, request, parsers):
        raise NotImplementedError('.select_parser() must be implemented')

    def select_renderer(self, request, renderers, format_suffix=None):
        raise NotImplementedError('.select_renderer() must be implemented')


class DefaultContentNegotiation(BaseContentNegotiation):
    settings = api_settings

    def select_parser(self, request, parsers):
        """
        Given a list of parsers and a media type, return the appropriate
        parser to handle the incoming request.
        """
        for parser in parsers:
            if media_type_matches(parser.media_type, request.content_type):
                return parser
        return None

    def select_renderer(self, request, renderers, format_suffix=None):
        """
        Given a request and a list of renderers, return a two-tuple of:
        (renderer, media type).
        """
        # Allow URL style format override.  eg. "?format=json
        format_query_param = self.settings.URL_FORMAT_OVERRIDE
        format = format_suffix or request.query_params.get(format_query_param)

        if format:
            renderers = self.filter_renderers(renderers, format)

        accepts = self.get_accept_list(request)

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) * len(self.renderers)
        for media_type_set in order_by_precedence(accepts):
            for renderer in renderers:
                for media_type in media_type_set:
                    if media_type_matches(renderer.media_type, media_type):
                        # Return the most specific media type as accepted.
                        if (
                            _MediaType(renderer.media_type).precedence >
                            _MediaType(media_type).precedence
                        ):
                            # Eg client requests '*/*'
                            # Accepted media type is 'application/json'
                            return renderer, renderer.media_type
                        else:
                            # Eg client requests 'application/json; indent=8'
                            # Accepted media type is 'application/json; indent=8'
                            return renderer, media_type

        raise exceptions.NotAcceptable(available_renderers=renderers)

    def filter_renderers(self, renderers, format):
        """
        If there is a '.json' style format suffix, filter the renderers
        so that we only negotiation against those that accept that format.
        """
        renderers = [renderer for renderer in renderers
                     if renderer.format == format]
        if not renderers:
            raise Http404
        return renderers

    def get_accept_list(self, request):
        """
        Given the incoming request, return a tokenised list of media
        type strings.

        Allows URL style accept override.  eg. "?accept=application/json"
        """
        header = request.META.get('HTTP_ACCEPT', '*/*')
        header = request.query_params.get(self.settings.URL_ACCEPT_OVERRIDE, header)
        return [token.strip() for token in header.split(',')]
