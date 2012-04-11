"""
The :mod:`request` module provides a :class:`Request` class used to wrap the standard `request`
object received in all the views.

The wrapped request then offers a richer API, in particular :

    - content automatically parsed according to `Content-Type` header,
      and available as :meth:`.DATA<Request.DATA>`
    - full support of PUT method, including support for file uploads
    - form overloading of HTTP method, content type and content
"""
from StringIO import StringIO

from django.contrib.auth.models import AnonymousUser

from djangorestframework import status
from djangorestframework.utils.mediatypes import is_form_media_type


__all__ = ('Request',)


class Empty:
    pass


def _hasattr(obj, name):
    return not getattr(obj, name) is Empty


class Request(object):
    """
    Wrapper allowing to enhance a standard `HttpRequest` instance.

    Kwargs:
        - request(HttpRequest). The original request instance.
        - parsers(list/tuple). The parsers to use for parsing the request content.
        - authentications(list/tuple). The authentications used to try authenticating the request's user.
    """

    _USE_FORM_OVERLOADING = True
    _METHOD_PARAM = '_method'
    _CONTENTTYPE_PARAM = '_content_type'
    _CONTENT_PARAM = '_content'

    def __init__(self, request=None, parsers=None, authentication=None):
        self._request = request
        self.parsers = parsers or ()
        self.authentication = authentication or ()
        self._data = Empty
        self._files = Empty
        self._method = Empty
        self._content_type = Empty
        self._stream = Empty

    def get_parsers(self):
        """
        Instantiates and returns the list of parsers the request will use.
        """
        return [parser() for parser in self.parsers]

    def get_authentications(self):
        """
        Instantiates and returns the list of parsers the request will use.
        """
        return [authentication() for authentication in self.authentication]

    @property
    def method(self):
        """
        Returns the HTTP method.

        This allows the `method` to be overridden by using a hidden `form`
        field on a form POST request.
        """
        if not _hasattr(self, '_method'):
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
        if not _hasattr(self, '_content_type'):
            self._load_method_and_content_type()
        return self._content_type

    @property
    def stream(self):
        """
        Returns an object that may be used to stream the request content.
        """
        if not _hasattr(self, '_stream'):
            self._load_stream()
        return self._stream

    @property
    def DATA(self):
        """
        Parses the request body and returns the data.

        Similar to ``request.POST``, except that it handles arbitrary parsers,
        and also works on methods other than POST (eg PUT).
        """
        if not _hasattr(self, '_data'):
            self._load_data_and_files()
        return self._data

    @property
    def FILES(self):
        """
        Parses the request body and returns the files.
        Similar to ``request.FILES``, except that it handles arbitrary parsers,
        and also works on methods other than POST (eg PUT).
        """
        if not _hasattr(self, '_files'):
            self._load_data_and_files()
        return self._files

    @property
    def user(self):
        """
        Returns the :obj:`user` for the current request, authenticated
        with the set of :class:`authentication` instances applied to the :class:`Request`.
        """
        if not hasattr(self, '_user'):
            self._user = self._authenticate()
        return self._user

    def _load_data_and_files(self):
        """
        Parses the request content into self.DATA and self.FILES.
        """
        if not _hasattr(self, '_content_type'):
            self._load_method_and_content_type()

        if not _hasattr(self, '_data'):
            (self._data, self._files) = self._parse()

    def _load_method_and_content_type(self):
        """
        Sets the method and content_type, and then check if they've been overridden.
        """
        self._content_type = self.META.get('HTTP_CONTENT_TYPE', self.META.get('CONTENT_TYPE', ''))
        self._perform_form_overloading()
        # if the HTTP method was not overloaded, we take the raw HTTP method
        if not _hasattr(self, '_method'):
            self._method = self._request.method

    def _load_stream(self):
        try:
            content_length = int(self.META.get('CONTENT_LENGTH',
                                    self.META.get('HTTP_CONTENT_LENGTH')))
        except (ValueError, TypeError):
            content_length = 0

        if content_length == 0:
            self._stream = None
        elif hasattr(self._request, 'read'):
            self._stream = self._request
        else:
            self._stream = StringIO(self.raw_post_data)

    def _perform_form_overloading(self):
        """
        If this is a form POST request, then we need to check if the method and
        content/content_type have been overridden by setting them in hidden
        form fields or not.
        """

        # We only need to use form overloading on form POST requests.
        if (not self._USE_FORM_OVERLOADING
            or self._request.method != 'POST'
            or not is_form_media_type(self._content_type)):
            return

        # At this point we're committed to parsing the request as form data.
        self._data = self._request.POST
        self._files = self._request.FILES

        # Method overloading - change the method and remove the param from the content.
        if self._METHOD_PARAM in self._data:
            # NOTE: `pop` on a `QueryDict` returns a list of values.
            self._method = self._data.pop(self._METHOD_PARAM)[0].upper()

        # Content overloading - modify the content type, and re-parse.
        if (self._CONTENT_PARAM in self._data and
            self._CONTENTTYPE_PARAM in self._data):
            self._content_type = self._data.pop(self._CONTENTTYPE_PARAM)[0]
            self._stream = StringIO(self._data.pop(self._CONTENT_PARAM)[0])
            (self._data, self._files) = self._parse()

    def _parse(self):
        """
        Parse the request content.

        May raise a 415 ImmediateResponse (Unsupported Media Type), or a
        400 ImmediateResponse (Bad Request).
        """
        if self.stream is None or self.content_type is None:
            return (None, None)

        for parser in self.get_parsers():
            if parser.can_handle_request(self.content_type):
                return parser.parse(self.stream, self.META, self.upload_handlers)

        self._raise_415_response(self._content_type)

    def _raise_415_response(self, content_type):
        """
        Raise a 415 response if we cannot parse the given content type.
        """
        from djangorestframework.response import ImmediateResponse

        raise ImmediateResponse(
            {
                'error': 'Unsupported media type in request \'%s\'.'
                % content_type
            },
            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def _authenticate(self):
        """
        Attempt to authenticate the request using each authentication instance in turn.
        Returns a ``User`` object, which may be ``AnonymousUser``.
        """
        for authentication in self.get_authentications():
            user = authentication.authenticate(self)
            if user:
                return user
        return AnonymousUser()

    def __getattr__(self, name):
        """
        Proxy other attributes to the underlying HttpRequest object.
        """
        return getattr(self._request, name)
