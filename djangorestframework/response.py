"""
The :mod:`response` module provides :class:`Response` and :class:`ImmediateResponse` classes.

`Response` is a subclass of `HttpResponse`, and can be similarly instantiated and returned
from any view. It is a bit smarter than Django's `HttpResponse`, for it renders automatically
its content to a serial format by using a list of :mod:`renderers`.

To determine the content type to which it must render, default behaviour is to use standard
HTTP Accept header content negotiation. But `Response` also supports overriding the content type
by specifying an ``_accept=`` parameter in the URL. Also, `Response` will ignore `Accept` headers
from Internet Explorer user agents and use a sensible browser `Accept` header instead.


`ImmediateResponse` is an exception that inherits from `Response`. It can be used
to abort the request handling (i.e. ``View.get``, ``View.put``, ...),
and immediately returning a response.
"""

from django.template.response import SimpleTemplateResponse
from django.core.handlers.wsgi import STATUS_CODE_TEXT

from djangorestframework.utils.mediatypes import order_by_precedence
from djangorestframework.utils import MSIE_USER_AGENT_REGEX
from djangorestframework import status


class NotAcceptable(Exception):
    pass


class Response(SimpleTemplateResponse):
    """
    An HttpResponse that may include content that hasn't yet been serialized.

    Kwargs:
        - content(object). The raw content, not yet serialized.
        This must be native Python data that renderers can handle.
        (e.g.: `dict`, `str`, ...)
        - renderers(list/tuple). The renderers to use for rendering the response content.
    """

    _ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params
    _IGNORE_IE_ACCEPT_HEADER = True

    def __init__(self, content=None, status=None, headers=None, view=None, request=None, renderers=None):
        # First argument taken by `SimpleTemplateResponse.__init__` is template_name,
        # which we don't need
        super(Response, self).__init__(None, status=status)

        self.raw_content = content
        self.has_content_body = content is not None
        self.headers = headers and headers[:] or []
        self.view = view
        self.request = request
        self.renderers = renderers

    def get_renderers(self):
        """
        Instantiates and returns the list of renderers the response will use.
        """
        return [renderer(self.view) for renderer in self.renderers]

    @property
    def rendered_content(self):
        """
        The final rendered content. Accessing this attribute triggers the
        complete rendering cycle: selecting suitable renderer, setting
        response's actual content type, rendering data.
        """
        renderer, media_type = self._determine_renderer()

        # Set the media type of the response
        self['Content-Type'] = renderer.media_type

        # Render the response content
        if self.has_content_body:
            return renderer.render(self.raw_content, media_type)
        return renderer.render()

    def render(self):
        try:
            return super(Response, self).render()
        except NotAcceptable:
            response = self._get_406_response()
            return response.render()

    @property
    def status_text(self):
        """
        Returns reason text corresponding to our HTTP response status code.
        Provided for convenience.
        """
        return STATUS_CODE_TEXT.get(self.status_code, '')

    def _determine_accept_list(self):
        """
        Returns a list of accepted media types. This list is determined from :

            1. overload with `_ACCEPT_QUERY_PARAM`
            2. `Accept` header of the request

        If those are useless, a default value is returned instead.
        """
        request = self.request

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
        Determines the appropriate renderer for the output, given the list of
        accepted media types, and the :attr:`renderers` set on this class.

        Returns a 2-tuple of `(renderer, media_type)`

        See: RFC 2616, Section 14
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
        """

        renderers = self.get_renderers()
        accepts = self._determine_accept_list()

        # Not acceptable response - Ignore accept header.
        if self.status_code == 406:
            return (renderers[0], renderers[0].media_type)

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) * len(self.renderers)
        for media_type_list in order_by_precedence(accepts):
            for renderer in renderers:
                for media_type in media_type_list:
                    if renderer.can_handle_response(media_type):
                        return renderer, media_type

        # No acceptable renderers were found
        raise NotAcceptable

    def _get_406_response(self):
        renderer = self.renderers[0]
        return Response(
            {
                'detail': 'Could not satisfy the client\'s Accept header',
                'available_types': [renderer.media_type
                                    for renderer in self.renderers]
            },
            status=status.HTTP_406_NOT_ACCEPTABLE,
            view=self.view, request=self.request, renderers=[renderer])
