"""Mixin classes that provide a determine_content(request) method to return the content type and content of a request.
We use this more generic behaviour to allow for overloaded content in POST forms.
"""

class ContentMixin(object):
    """Base class for all ContentMixin classes, which simply defines the interface they provide."""

    def determine_content(self, request):
        """If the request contains content return a tuple of (content_type, content) otherwise return None.
        Note that content_type may be None if it is unset.
        Must be overridden to be implemented."""
        raise NotImplementedError()


class StandardContentMixin(ContentMixin):
    """Standard HTTP request content behaviour.
    See RFC 2616 sec 4.3 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html#sec4.3"""

    def determine_content(self, request):
        """If the request contains content return a tuple of (content_type, content) otherwise return None.
        Note that content_type may be None if it is unset."""

        if not request.META.get('CONTENT_LENGTH', None) and not request.META.get('TRANSFER_ENCODING', None):
            return None
        return (request.META.get('CONTENT_TYPE', None), request.raw_post_data)


class OverloadedContentMixin(ContentMixin):
    """HTTP request content behaviour that also allows arbitrary content to be tunneled in form data."""
    
    """The name to use for the content override field in the POST form."""
    CONTENT_PARAM = '_content'

    """The name to use for the content-type override field in the POST form."""
    CONTENTTYPE_PARAM = '_contenttype'

    def determine_content(self, request):
        """If the request contains content return a tuple of (content_type, content) otherwise return None.
        Note that content_type may be None if it is unset."""
        if not request.META.get('CONTENT_LENGTH', None) and not request.META.get('TRANSFER_ENCODING', None):
            return None
        
        content_type = request.META.get('CONTENT_TYPE', None)

        if (request.method == 'POST' and self.CONTENT_PARAM and
            request.POST.get(self.CONTENT_PARAM, None) is not None):

            # Set content type if form contains a none empty FORM_PARAM_CONTENTTYPE field
            content_type = None
            if self.CONTENTTYPE_PARAM and request.POST.get(self.CONTENTTYPE_PARAM, None):
                content_type = request.POST.get(self.CONTENTTYPE_PARAM, None)

            return (content_type, request.POST[self.CONTENT_PARAM])

        return (content_type, request.raw_post_data)