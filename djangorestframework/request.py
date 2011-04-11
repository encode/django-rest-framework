from djangorestframework.mediatypes import MediaType
#from djangorestframework.requestparsing import parse, load_parser
from django.http.multipartparser import LimitBytes
from StringIO import StringIO

class RequestMixin(object):
    """Delegate class that supplements an HttpRequest object with additional behaviour."""

    USE_FORM_OVERLOADING = True
    METHOD_PARAM = "_method"
    CONTENTTYPE_PARAM = "_content_type"
    CONTENT_PARAM = "_content"

    def _get_method(self):
        """
        Returns the HTTP method for the current view.
        """
        if not hasattr(self, '_method'):
            self._method = self.request.method
        return self._method


    def _set_method(self, method):
        """
        Set the method for the current view.
        """
        self._method = method


    def _get_content_type(self):
        """
        Returns a MediaType object, representing the request's content type header.
        """
        if not hasattr(self, '_content_type'):
            content_type = self.request.META.get('HTTP_CONTENT_TYPE', self.request.META.get('CONTENT_TYPE', ''))
            self._content_type = MediaType(content_type)
        return self._content_type


    def _set_content_type(self, content_type):
        """
        Set the content type.  Should be a MediaType object.
        """
        self._content_type = content_type


    def _get_accept(self):
        """
        Returns a list of MediaType objects, representing the request's accept header.
        """
        if not hasattr(self, '_accept'):
            accept = self.request.META.get('HTTP_ACCEPT', '*/*')
            self._accept = [MediaType(elem) for elem in accept.split(',')]
        return self._accept


    def _set_accept(self):
        """
        Set the acceptable media types.  Should be a list of MediaType objects.
        """
        self._accept = accept


    def _get_stream(self):
        """
        Returns an object that may be used to stream the request content.
        """
        if not hasattr(self, '_stream'):
            request = self.request

            # Currently only supports parsing request body as a stream with 1.3
            if hasattr(request, 'read'):
                # It's not at all clear if this needs to be byte limited or not.
                # Maybe I'm just being dumb but it looks to me like there's some issues
                # with that in Django.
                #
                # Either:
                #   1. It *can't* be treated as a limited byte stream, and you _do_ need to
                #      respect CONTENT_LENGTH, in which case that ought to be documented,
                #      and there probably ought to be a feature request for it to be
                #      treated as a limited byte stream.
                #   2. It *can* be treated as a limited byte stream, in which case there's a
                #      minor bug in the test client, and potentially some redundant
                #      code in MultipartParser.
                #
                #   It's an issue because it affects if you can pass a request off to code that
                #   does something like:
                #
                #   while stream.read(BUFFER_SIZE):
                #       [do stuff]
                #
                #try:
                #    content_length = int(request.META.get('CONTENT_LENGTH',0))
                #except (ValueError, TypeError):
                #    content_length = 0
                # self._stream = LimitedStream(request, content_length)
                self._stream = request
            else:
                self._stream = StringIO(request.raw_post_data)
        return self._stream


    def _set_stream(self, stream):
        """
        Set the stream representing the request body.
        """
        self._stream = stream


    def _get_raw_content(self):
        """
        Returns the parsed content of the request
        """
        if not hasattr(self, '_raw_content'):
            self._raw_content = self.parse(self.stream, self.content_type)
        return self._raw_content


    def _get_content(self):
        """
        Returns the parsed and validated content of the request
        """
        if not hasattr(self, '_content'):
            self._content = self.validate(self.RAW_CONTENT)

        return self._content


    def perform_form_overloading(self):
        """
        Check the request to see if it is using form POST '_method'/'_content'/'_content_type' overrides.
        If it is then alter self.method, self.content_type, self.CONTENT to reflect that rather than simply
        delegating them to the original request.
        """
        if not self.USE_FORM_OVERLOADING or self.method != 'POST' or not self.content_type.is_form():
            return

        content = self.RAW_CONTENT
        if self.METHOD_PARAM in content:
            self.method = content[self.METHOD_PARAM].upper()
            del self._raw_content[self.METHOD_PARAM]

        if self.CONTENT_PARAM in content and self.CONTENTTYPE_PARAM in content:
            self._content_type = MediaType(content[self.CONTENTTYPE_PARAM])
            self._stream = StringIO(content[self.CONTENT_PARAM])
            del(self._raw_content)

    def parse(self, stream, content_type):
        """
        Parse the request content.

        May raise a 415 ResponseException (Unsupported Media Type),
        or a 400 ResponseException (Bad Request).
        """
        parsers = as_tuple(self.parsers)

        parser = None
        for parser_cls in parsers:
            if parser_cls.handles(content_type):
                parser = parser_cls(self)
                break

        if parser is None:
            raise ResponseException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                    {'error': 'Unsupported media type in request \'%s\'.' %
                                     content_type.media_type})

        return parser.parse(stream)

    @property
    def parsed_media_types(self):
        """Return an list of all the media types that this view can parse."""
        return [parser.media_type for parser in self.parsers]
    
    @property
    def default_parser(self):
        """Return the view's most preffered emitter.
        (This has no behavioural effect, but is may be used by documenting emitters)"""        
        return self.parsers[0]

    method = property(_get_method, _set_method)
    content_type = property(_get_content_type, _set_content_type)
    accept = property(_get_accept, _set_accept)
    stream = property(_get_stream, _set_stream)
    RAW_CONTENT = property(_get_raw_content)
    CONTENT = property(_get_content)



