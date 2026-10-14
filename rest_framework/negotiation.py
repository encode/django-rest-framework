"""
Content negotiation deals with selecting an appropriate renderer given the
incoming request.  Typically this will be based on the request's Accept header.
"""
from django.http import Http404

from rest_framework import exceptions
from rest_framework.settings import api_settings
from rest_framework.utils.mediatypes import (
    _MediaType, media_type_matches, order_parsed_by_precedence
)


class BaseContentNegotiation:
    def select_parser(self, request, parsers):
        raise NotImplementedError('.select_parser() must be implemented')

    def select_renderer(self, request, renderers, format_suffix=None):
        raise NotImplementedError('.select_renderer() must be implemented')


class DefaultContentNegotiation(BaseContentNegotiation):
    settings = api_settings

    max_accept_header_length = 8192
    max_accept_tokens = 64
    max_media_type_length = 256

    def select_parser(self, request, parsers):
        """
        Given a list of parsers and a media type, return the appropriate
        parser to handle the incoming request.
        """
        content_type = request.content_type
        if content_type and len(content_type) > self.max_media_type_length:
            # Refuse rather than parse. Returning None results in a 415.
            return None
        for parser in parsers:
            if media_type_matches(parser.media_type, content_type):
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

        accepts = self._get_parsed_accept_list(request)

        # Parse each renderer's (constant) media type once, not once per token.
        renderer_media_types = [
            (renderer, _MediaType(renderer.media_type)) for renderer in renderers
        ]

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) * len(self.renderers)
        for media_type_set in order_parsed_by_precedence(accepts):
            for renderer, renderer_media_type in renderer_media_types:
                for media_type_wrapper in media_type_set:
                    if renderer_media_type.match(media_type_wrapper):
                        media_type = media_type_wrapper.orig
                        # Return the most specific media type as accepted.
                        if (
                            renderer_media_type.precedence >
                            media_type_wrapper.precedence
                        ):
                            # Eg client requests '*/*'
                            # Accepted media type is 'application/json'
                            full_media_type = ';'.join(
                                (renderer.media_type,) +
                                tuple(
                                    f'{key}={value}'
                                    for key, value in media_type_wrapper.params.items()
                                )
                            )
                            return renderer, full_media_type
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
        Given the incoming request, return a tokenized list of media
        type strings.
        """
        header = request.headers.get('accept', '*/*')
        if len(header) > self.max_accept_header_length:
            # Truncate at a separator, so a truncated tail cannot be read as a
            # valid media type. split() then only ever runs on a bounded prefix.
            cut = header.rfind(',', 0, self.max_accept_header_length)
            header = header[:cut + 1] if cut != -1 else ''
        tokens = []
        for token in header.split(','):
            token = token.strip()
            if not token or len(token) > self.max_media_type_length:
                # Skip (don't break): an over-long leading token should not
                # discard the usable media types that follow it.
                continue
            tokens.append(token)
            if len(tokens) >= self.max_accept_tokens:
                break
        return tokens

    def _get_parsed_accept_list(self, request):
        """
        Parse the Accept tokens into ``_MediaType`` objects exactly once per
        request, reusing them for the forced 406 re-negotiation instead of
        re-parsing (and without a process-global cache of client input).
        """
        parsed = getattr(request, '_parsed_accept_list', None)
        if parsed is None:
            parsed = [_MediaType(token) for token in self.get_accept_list(request)]
            try:
                request._parsed_accept_list = parsed
            except Exception:
                pass
        return parsed
