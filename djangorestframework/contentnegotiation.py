from djangorestframework import exceptions
from djangorestframework.settings import api_settings
from djangorestframework.utils.mediatypes import order_by_precedence
import re

MSIE_USER_AGENT_REGEX = re.compile(r'^Mozilla/[0-9]+\.[0-9]+ \([^)]*; MSIE [0-9]+\.[0-9]+[a-z]?;[^)]*\)(?!.* Opera )')


class BaseContentNegotiation(object):
    def determine_renderer(self, request, renderers):
        raise NotImplementedError('.determine_renderer() must be implemented')


class DefaultContentNegotiation(object):
    settings = api_settings

    def negotiate(self, request, renderers):
        """
        Given a request and a list of renderers, return a two-tuple of:
        (renderer, media type).
        """
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
