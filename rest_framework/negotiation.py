from rest_framework import exceptions
from rest_framework.settings import api_settings
from rest_framework.utils.mediatypes import order_by_precedence


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
            return self.unforced_negotiate(request, renderers, format)
        except (exceptions.InvalidFormat, exceptions.NotAcceptable):
            if force:
                return (renderers[0], renderers[0].media_type)
            raise

    def unforced_negotiate(self, request, renderers, format=None):
        """
        As `.negotiate()`, but does not take the optional `force` agument,
        or suppress exceptions.
        """
        # Allow URL style format override.  eg. "?format=json
        format = format or request.GET.get(self.settings.URL_FORMAT_OVERRIDE)

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
                    if renderer.can_handle_media_type(media_type):
                        return renderer, media_type

        raise exceptions.NotAcceptable(available_renderers=renderers)

    def filter_renderers(self, renderers, format):
        """
        If there is a '.json' style format suffix, filter the renderers
        so that we only negotiation against those that accept that format.
        """
        renderers = [renderer for renderer in renderers
                     if renderer.can_handle_format(format)]
        if not renderers:
            raise exceptions.InvalidFormat(format)
        return renderers

    def get_accept_list(self, request):
        """
        Given the incoming request, return a tokenised list of media
        type strings.

        Allows URL style accept override.  eg. "?accept=application/json"
        """
        header = request.META.get('HTTP_ACCEPT', '*/*')
        header = request.GET.get(self.settings.URL_ACCEPT_OVERRIDE, header)
        return [token.strip() for token in header.split(',')]
