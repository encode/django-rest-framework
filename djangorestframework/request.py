"""
The :mod:`request` module provides a :class:`Request` class that can be used 
to wrap the standard `request` object received in all the views, and upgrade its API.

The wrapped request then offer the following :

    - content automatically parsed according to `Content-Type` header, and available as :meth:`.DATA<Request.DATA>`
    - full support of PUT method, including support for file uploads
    - form overloading of HTTP method, content type and content
"""

from django.http import HttpRequest

from djangorestframework.response import ImmediateResponse
from djangorestframework import status
from djangorestframework.utils.mediatypes import is_form_media_type, order_by_precedence
from djangorestframework.utils import as_tuple

from StringIO import StringIO


__all__ = ('Request',)


class Request(object):
    """
    A wrapper allowing to enhance Django's standard HttpRequest.
    """

    _USE_FORM_OVERLOADING = True
    _METHOD_PARAM = '_method'
    _CONTENTTYPE_PARAM = '_content_type'
    _CONTENT_PARAM = '_content'

    def __init__(self, request=None, parsers=None):
        """
        `parsers` is a list/tuple of parser instances and represents the set of psrsers
        that the response can handle.
        """
        self.request = request
        if parsers is not None:
            self.parsers = parsers

    @property
    def method(self):
        """
        Returns the HTTP method.

        This allows the `method` to be overridden by using a hidden `form` field
        on a form POST request.
        """
        if not hasattr(self, '_method'):
            self._load_method_and_content_type()
        return self._method

    @property
    def content_type(self):
        """
        Returns the content type header.

        This should be used instead of ``request.META.get('HTTP_CONTENT_TYPE')``,
        as it allows the content type to be overridden by using a hidden form
        field on a form POST request.
        """
        if not hasattr(self, '_content_type'):
            self._load_method_and_content_type()
        return self._content_type

    @property
    def DATA(self):
        """
        Parses the request body and returns the data.

        Similar to ``request.POST``, except that it handles arbitrary parsers,
        and also works on methods other than POST (eg PUT).
        """
        if not hasattr(self, '_data'):
            self._load_data_and_files()
        return self._data

    @property
    def FILES(self):
        """
        Parses the request body and returns the files.
        Similar to ``request.FILES``, except that it handles arbitrary parsers,
        and also works on methods other than POST (eg PUT).
        """
        if not hasattr(self, '_files'):
            self._load_data_and_files()
        return self._files

    def _load_data_and_files(self):
        """
        Parses the request content into self.DATA and self.FILES.
        """
        if not hasattr(self, '_content_type'):
            self._load_method_and_content_type()

        if not hasattr(self, '_data'):
            (self._data, self._files) = self._parse(self._get_stream(), self._content_type)

    def _load_method_and_content_type(self):
        """
        Sets the method and content_type, and then check if they've been overridden.
        """
        self._content_type = self.META.get('HTTP_CONTENT_TYPE', self.META.get('CONTENT_TYPE', ''))
        self._perform_form_overloading()
        # if the HTTP method was not overloaded, we take the raw HTTP method 
        if not hasattr(self, '_method'):
            self._method = self.request.method

    def _get_stream(self):
        """
        Returns an object that may be used to stream the request content.
        """

        try:
            content_length = int(self.META.get('CONTENT_LENGTH', self.META.get('HTTP_CONTENT_LENGTH')))
        except (ValueError, TypeError):
            content_length = 0

        # TODO: Add 1.3's LimitedStream to compat and use that.
        # NOTE: Currently only supports parsing request body as a stream with 1.3
        if content_length == 0:
            return None
        elif hasattr(self, 'read'):
            return self
        return StringIO(self.raw_post_data)

    def _perform_form_overloading(self):
        """
        If this is a form POST request, then we need to check if the method and content/content_type have been
        overridden by setting them in hidden form fields or not.
        """

        # We only need to use form overloading on form POST requests.
        if (not self._USE_FORM_OVERLOADING or self.request.method != 'POST'
                                or not is_form_media_type(self._content_type)):
            return

        # At this point we're committed to parsing the request as form data.
        self._data = data = self.POST.copy()
        self._files = self.FILES

        # Method overloading - change the method and remove the param from the content.
        if self._METHOD_PARAM in data:
            # NOTE: unlike `get`, `pop` on a `QueryDict` seems to return a list of values.
            self._method = self._data.pop(self._METHOD_PARAM)[0].upper()

        # Content overloading - modify the content type, and re-parse.
        if self._CONTENT_PARAM in data and self._CONTENTTYPE_PARAM in data:
            self._content_type = self._data.pop(self._CONTENTTYPE_PARAM)[0]
            stream = StringIO(self._data.pop(self._CONTENT_PARAM)[0])
            (self._data, self._files) = self._parse(stream, self._content_type)

    def _parse(self, stream, content_type):
        """
        Parse the request content.

        May raise a 415 ImmediateResponse (Unsupported Media Type), or a 400 ImmediateResponse (Bad Request).
        """
        if stream is None or content_type is None:
            return (None, None)

        for parser in as_tuple(self.parsers):
            if parser.can_handle_request(content_type):
                return parser.parse(stream)

        raise ImmediateResponse(content={'error':
                            'Unsupported media type in request \'%s\'.' % content_type},
                        status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    @property
    def _parsed_media_types(self):
        """
        Return a list of all the media types that this view can parse.
        """
        return [parser.media_type for parser in self.parsers]

    @property
    def _default_parser(self):
        """
        Return the view's default parser class.
        """
        return self.parsers[0]

    def _get_parsers(self):
        """
        This just provides a default when parsers havent' been set.
        """
        if hasattr(self, '_parsers'):
            return self._parsers
        return ()

    def _set_parsers(self, value):
        self._parsers = value

    parsers = property(_get_parsers, _set_parsers)

    def __getattr__(self, name):
        """
        When an attribute is not present on the calling instance, try to get it
        from the original request.
        """
        if hasattr(self.request, name):
            return getattr(self.request, name)
        else:
            return super(Request, self).__getattribute__(name)
