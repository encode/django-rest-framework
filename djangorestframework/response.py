"""
The :mod:`response` module provides Response classes you can use in your
views to return a certain HTTP response. Typically a response is *rendered*
into a HTTP response depending on what renderers are set on your view and
als depending on the accept header of the request.
"""

from django.template.response import SimpleTemplateResponse
from django.core.handlers.wsgi import STATUS_CODE_TEXT

from djangorestframework.utils.mediatypes import order_by_precedence
from djangorestframework.utils import MSIE_USER_AGENT_REGEX
from djangorestframework import status


__all__ = ('Response', 'ErrorResponse')


class Response(SimpleTemplateResponse):
    """
    An HttpResponse that may include content that hasn't yet been serialized.
    """

    _ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params
    _IGNORE_IE_ACCEPT_HEADER = True

    def __init__(self, content=None, status=None, request=None, renderers=None):
        """
        content is the raw content.

        The set of renderers that the response can handle.

        Should be a tuple/list of classes as described in the :mod:`renderers` module.
        """
        # First argument taken by `SimpleTemplateResponse.__init__` is template_name,
        # which we don't need
        super(Response, self).__init__(None, status=status)
        # We need to store our content in raw content to avoid overriding HttpResponse's
        # `content` property
        self.raw_content = content 
        self.has_content_body = content is not None
        self.request = request
        if renderers is not None:
            self.renderers = renderers
        # TODO: must go
        self.view = None

    # TODO: wrap this behavior around dispatch(), ensuring it works
    # out of the box with existing Django classes that use render_to_response.
    @property
    def rendered_content(self):
        """
        """
        renderer, media_type = self._determine_renderer()
        # TODO: renderer *could* override media_type in .render() if required.

        # Set the media type of the response
        self['Content-Type'] = renderer.media_type

        # Render the response content
        if self.has_content_body:
            return renderer.render(self.raw_content, media_type)
        return renderer.render()

    @property
    def status_text(self):
        """
        Return reason text corresponding to our HTTP response status code.
        Provided for convenience.
        """
        return STATUS_CODE_TEXT.get(self.status, '')

    def _determine_accept_list(self):
        request = self.request
        if request is None:
            return ['*/*']

        if self._ACCEPT_QUERY_PARAM and request.GET.get(self._ACCEPT_QUERY_PARAM, None):
            # Use _accept parameter override
            return [request.GET.get(self._ACCEPT_QUERY_PARAM)]
        elif (self._IGNORE_IE_ACCEPT_HEADER and
              'HTTP_USER_AGENT' in request.META and
              MSIE_USER_AGENT_REGEX.match(request.META['HTTP_USER_AGENT'])):
            # Ignore MSIE's broken accept behavior and do something sensible instead
            return ['text/html', '*/*']
        elif 'HTTP_ACCEPT' in request.META:
            # Use standard HTTP Accept negotiation
            return [token.strip() for token in request.META['HTTP_ACCEPT'].split(',')]
        else:
            # No accept header specified
            return ['*/*']

    def _determine_renderer(self):
        """
        Determines the appropriate renderer for the output, given the client's 'Accept' header,
        and the :attr:`renderers` set on this class.

        Returns a 2-tuple of `(renderer, media_type)`

        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
        """
        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) * len(self.renderers)
        renderers = [renderer_cls(self.view) for renderer_cls in self.renderers]

        for media_type_list in order_by_precedence(self._determine_accept_list()):
            for renderer in renderers:
                for media_type in media_type_list:
                    if renderer.can_handle_response(media_type):
                        return renderer, media_type

        # No acceptable renderers were found
        raise ErrorResponse(content={'detail': 'Could not satisfy the client\'s Accept header',
                                 'available_types': self._rendered_media_types},
                        status=status.HTTP_406_NOT_ACCEPTABLE,
                        renderers=self.renderers)

    def _get_renderers(self):
        """
        This just provides a default when renderers havent' been set.
        """
        if hasattr(self, '_renderers'):
            return self._renderers
        return ()

    def _set_renderers(self, value):
        self._renderers = value

    renderers = property(_get_renderers, _set_renderers)

    @property
    def _rendered_media_types(self):
        """
        Return an list of all the media types that this response can render.
        """
        return [renderer.media_type for renderer in self.renderers]

    @property
    def _rendered_formats(self):
        """
        Return a list of all the formats that this response can render.
        """
        return [renderer.format for renderer in self.renderers]

    @property
    def _default_renderer(self):
        """
        Return the response's default renderer class.
        """
        return self.renderers[0]


class ErrorResponse(Response, BaseException):
    """
    An exception representing an Response that should be returned immediately.
    Any content should be serialized as-is, without being filtered.
    """
    pass

