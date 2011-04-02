from djangorestframework.mediatypes import MediaType
#from djangorestframework.requestparsing import parse, load_parser
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
            if hasattr(self.request, 'read'):
                self._stream = self.request
            else:
                self._stream = StringIO(self.request.raw_post_data)
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

    method = property(_get_method, _set_method)
    content_type = property(_get_content_type, _set_content_type)
    accept = property(_get_accept, _set_accept)
    stream = property(_get_stream, _set_stream)
    RAW_CONTENT = property(_get_raw_content)
    CONTENT = property(_get_content)



