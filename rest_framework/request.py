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

from django.http.multipartparser import parse_header
from rest_framework import exceptions
from rest_framework.settings import api_settings


def is_form_media_type(media_type):
    """
    Return True if the media type is a valid form media type.
    """
    base_media_type, params = parse_header(media_type)
    return base_media_type == 'application/x-www-form-urlencoded' or \
           base_media_type == 'multipart/form-data'


class Empty(object):
    """
    Placeholder for unset attributes.
    Cannot use `None`, as that may be a valid value.
    """
    pass


def _hasattr(obj, name):
    return not getattr(obj, name) is Empty


def clone_request(request, method):
    """
    Internal helper method to clone a request, replacing with a different
    HTTP method.  Used for checking permissions against other methods.
    """
    ret = Request(request._request,
                  request.parsers,
                  request.authenticators,
                  request.parser_context)
    ret._data = request._data
    ret._files = request._files
    ret._content_type = request._content_type
    ret._stream = request._stream
    ret._method = method
    if hasattr(request, '_user'):
        ret._user = request._user
    if hasattr(request, '_auth'):
        ret._auth = request._auth
    return ret


class Request(object):
    """
    Wrapper allowing to enhance a standard `HttpRequest` instance.

    Kwargs:
        - request(HttpRequest). The original request instance.
        - parsers_classes(list/tuple). The parsers to use for parsing the
          request content.
        - authentication_classes(list/tuple). The authentications used to try
          authenticating the request's user.
    """

    _METHOD_PARAM = api_settings.FORM_METHOD_OVERRIDE
    _CONTENT_PARAM = api_settings.FORM_CONTENT_OVERRIDE
    _CONTENTTYPE_PARAM = api_settings.FORM_CONTENTTYPE_OVERRIDE

    def __init__(self, request, parsers=None, authenticators=None,
                 negotiator=None, parser_context=None):
        self._request = request
        self.parsers = parsers or ()
        self.authenticators = authenticators or ()
        self.negotiator = negotiator or self._default_negotiator()
        self.parser_context = parser_context
        self._data = Empty
        self._files = Empty
        self._method = Empty
        self._content_type = Empty
        self._stream = Empty

        if self.parser_context is None:
            self.parser_context = {}
        self.parser_context['request'] = self

    def _default_negotiator(self):
        return api_settings.DEFAULT_CONTENT_NEGOTIATION_CLASS()

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

        This should be used instead of `request.META.get('HTTP_CONTENT_TYPE')`,
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
    def QUERY_PARAMS(self):
        """
        More semantically correct name for request.GET.
        """
        return self._request.GET

    @property
    def DATA(self):
        """
        Parses the request body and returns the data.

        Similar to usual behaviour of `request.POST`, except that it handles
        arbitrary parsers, and also works on methods other than POST (eg PUT).
        """
        if not _hasattr(self, '_data'):
            self._load_data_and_files()
        return self._data

    @property
    def FILES(self):
        """
        Parses the request body and returns any files uploaded in the request.

        Similar to usual behaviour of `request.FILES`, except that it handles
        arbitrary parsers, and also works on methods other than POST (eg PUT).
        """
        if not _hasattr(self, '_files'):
            self._load_data_and_files()
        return self._files

    @property
    def user(self):
        """
        Returns the user associated with the current request, as authenticated
        by the authentication classes provided to the request.
        """
        if not hasattr(self, '_user'):
            self._user, self._auth = self._authenticate()
        return self._user

    @property
    def auth(self):
        """
        Returns any non-user authentication information associated with the
        request, such as an authentication token.
        """
        if not hasattr(self, '_auth'):
            self._user, self._auth = self._authenticate()
        return self._auth

    def _load_data_and_files(self):
        """
        Parses the request content into self.DATA and self.FILES.
        """
        if not _hasattr(self, '_content_type'):
            self._load_method_and_content_type()

        if not _hasattr(self, '_data'):
            self._data, self._files = self._parse()

    def _load_method_and_content_type(self):
        """
        Sets the method and content_type, and then check if they've
        been overridden.
        """
        self._content_type = self.META.get('HTTP_CONTENT_TYPE',
                                           self.META.get('CONTENT_TYPE', ''))
        self._perform_form_overloading()
        # if the HTTP method was not overloaded, we take the raw HTTP method
        if not _hasattr(self, '_method'):
            self._method = self._request.method

    def _load_stream(self):
        """
        Return the content body of the request, as a stream.
        """
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

        USE_FORM_OVERLOADING = (
            self._METHOD_PARAM or
            (self._CONTENT_PARAM and self._CONTENTTYPE_PARAM)
        )

        # We only need to use form overloading on form POST requests.
        if (not USE_FORM_OVERLOADING
            or self._request.method != 'POST'
            or not is_form_media_type(self._content_type)):
            return

        # At this point we're committed to parsing the request as form data.
        self._data = self._request.POST
        self._files = self._request.FILES

        # Method overloading - change the method and remove the param from the content.
        if (self._METHOD_PARAM and
            self._METHOD_PARAM in self._data):
            self._method = self._data[self._METHOD_PARAM].upper()

        # Content overloading - modify the content type, and force re-parse.
        if (self._CONTENT_PARAM and
            self._CONTENTTYPE_PARAM and
            self._CONTENT_PARAM in self._data and
            self._CONTENTTYPE_PARAM in self._data):
            self._content_type = self._data[self._CONTENTTYPE_PARAM]
            self._stream = StringIO(self._data[self._CONTENT_PARAM])
            self._data, self._files = (Empty, Empty)

    def _parse(self):
        """
        Parse the request content, returning a two-tuple of (data, files)

        May raise an `UnsupportedMediaType`, or `ParseError` exception.
        """
        stream = self.stream
        media_type = self.content_type

        if stream is None or media_type is None:
            return (None, None)

        parser = self.negotiator.select_parser(self, self.parsers)

        if not parser:
            raise exceptions.UnsupportedMediaType(media_type)

        parsed = parser.parse(stream, media_type, self.parser_context)

        # Parser classes may return the raw data, or a
        # DataAndFiles object.  Unpack the result as required.
        try:
            return (parsed.data, parsed.files)
        except AttributeError:
            return (parsed, None)

    def _authenticate(self):
        """
        Attempt to authenticate the request using each authentication instance in turn.
        Returns a two-tuple of (user, authtoken).
        """
        for authenticator in self.authenticators:
            user_auth_tuple = authenticator.authenticate(self)
            if not user_auth_tuple is None:
                return user_auth_tuple
        return self._not_authenticated()

    def _not_authenticated(self):
        """
        Return a two-tuple of (user, authtoken), representing an
        unauthenticated request.

        By default this will be (AnonymousUser, None).
        """
        if api_settings.UNAUTHENTICATED_USER:
            user = api_settings.UNAUTHENTICATED_USER()
        else:
            user = None

        if api_settings.UNAUTHENTICATED_TOKEN:
            auth = api_settings.UNAUTHENTICATED_TOKEN()
        else:
            auth = None

        return (user, auth)

    def __getattr__(self, attr):
        """
        Proxy other attributes to the underlying HttpRequest object.
        """
        return getattr(self._request, attr)
