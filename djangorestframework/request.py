"""
The :mod:`request` module provides a `Request` class that can be used
to replace the standard Django request passed to the views.
This replacement `Request` provides many facilities, like automatically
parsed request content, form overloading of method/content type/content,
better support for HTTP PUT method. 
"""

from django.http import HttpRequest

from djangorestframework.utils.mediatypes import is_form_media_type, order_by_precedence
from djangorestframework.utils import as_tuple

from StringIO import StringIO


__all__ = ('Request')


def request_class_factory(request):
    """
    Builds and returns a request class, to be used as a replacement of Django's built-in.
    
    In fact :class:`request.Request` needs to be mixed-in with a subclass of `HttpRequest` for use,
    and we cannot do that before knowing which subclass of `HttpRequest` is used. So this function
    takes a request instance as only argument, and returns a properly mixed-in request class.
    """
    request_class = type(request)
    return type(request_class.__name__, (Request, request_class), {})


class Request(object):

    _USE_FORM_OVERLOADING = True
    _METHOD_PARAM = '_method'
    _CONTENTTYPE_PARAM = '_content_type'
    _CONTENT_PARAM = '_content'

    parsers = ()
    """
    The set of parsers that the request can handle.

    Should be a tuple/list of classes as described in the :mod:`parsers` module.
    """

    def __init__(self, request):
        # this allows to "copy" a request object into a new instance
        # of our custom request class.

        # First, we prepare the attributes to copy.
        attrs_dict = request.__dict__.copy()
        attrs_dict.pop('method', None)
        attrs_dict['_raw_method'] = request.method

        # Then, put them in the instance's own __dict__
        self.__dict__ = attrs_dict

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

    def _load_post_and_files(self):
        """
        Overrides the parent's `_load_post_and_files` to isolate it 
        from the form overloading mechanism (see: `_perform_form_overloading`).
        """
        # When self.POST or self.FILES are called they need to know the original
        # HTTP method, not our overloaded HTTP method. So, we save our overloaded
        # HTTP method and restore it after the call to parent.
        method_mem = getattr(self, '_method', None)
        self._method = self._raw_method
        super(Request, self)._load_post_and_files()
        if method_mem is None:
            del self._method
        else:
            self._method = method_mem

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
            self._method = self._raw_method

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
        if not self._USE_FORM_OVERLOADING or self._raw_method != 'POST' or not is_form_media_type(self._content_type):
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

        May raise a 415 ErrorResponse (Unsupported Media Type), or a 400 ErrorResponse (Bad Request).
        """
        if stream is None or content_type is None:
            return (None, None)

        parsers = as_tuple(self.parsers)

        for parser_cls in parsers:
            parser = parser_cls(self)
            if parser.can_handle_request(content_type):
                return parser.parse(stream)

        raise ErrorResponse(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            {'error': 'Unsupported media type in request \'%s\'.' %
                            content_type})

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
