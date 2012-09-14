from djangorestframework import exceptions
from djangorestframework.settings import api_settings
from djangorestframework.utils.mediatypes import order_by_precedence
from django.http import Http404
import re

MSIE_USER_AGENT_REGEX = re.compile(r'^Mozilla/[0-9]+\.[0-9]+ \([^)]*; MSIE [0-9]+\.[0-9]+[a-z]?;[^)]*\)(?!.* Opera )')


class BaseContentNegotiation(object):
    def negotiate(self, request, renderers, format=None, force=False):
        raise NotImplementedError('.negotiate() must be implemented')


class DefaultContentNegotiation(object):
    settings = api_settings

    def negotiate(self, request, renderers, format=None, force=False):
        """
        Given a request and a list of renderers, return a two-tuple of:
        (renderer, media type).

        If force is set, then suppress exceptions, and forcibly return a
        fallback renderer and media_type.
        """
        try:
            return self._negotiate(request, renderers, format)
        except (Http404, exceptions.NotAcceptable):
            if force:
                return (renderers[0], renderers[0].media_type)
            raise

    def _negotiate(self, request, renderers, format=None):
        """
        Actual implementation of negotiate, inside the 'force' wrapper.
        """
        renderers = self.filter_renderers(renderers, format)
        accepts = self.get_accept_list(request)

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) * len(self.renderers)
        for media_type_set in order_by_precedence(accepts):
            for renderer in renderers:
                for media_type in media_type_set:
                    if renderer.can_handle_media_type(media_type):
                        return renderer, media_type

        raise exceptions.NotAcceptable(available_renderers=renderers)

    def filter_renderers(self, renderers, format):
        """
        If there is a '.json' style format suffix, only use
        renderers that accept that format.
        """
        if not format:
            return renderers

        renderers = [renderer for renderer in renderers
                     if renderer.can_handle_format(format)]
        if not renderers:
            raise Http404()

    def get_accept_list(self, request):
        """
        Given the incoming request, return a tokenised list of
        media type strings.
        """
        if self.settings.URL_ACCEPT_OVERRIDE:
            # URL style accept override.  eg.  "?accept=application/json"
            override = request.GET.get(self.settings.URL_ACCEPT_OVERRIDE)
            if override:
                return [override]

        if (self.settings.IGNORE_MSIE_ACCEPT_HEADER and
            'HTTP_USER_AGENT' in request.META and
            MSIE_USER_AGENT_REGEX.match(request.META['HTTP_USER_AGENT']) and
            request.META.get('HTTP_X_REQUESTED_WITH', '').lower() != 'xmlhttprequest'):
            # Ignore MSIE's broken accept behavior except for AJAX requests
            # and do something sensible instead
            return ['text/html', '*/*']

        if 'HTTP_ACCEPT' in request.META:
            # Standard HTTP Accept negotiation
            # Accept header specified
            tokens = request.META['HTTP_ACCEPT'].split(',')
            return [token.strip() for token in tokens]

        # Standard HTTP Accept negotiation
        # No accept header specified
        return ['*/*']
