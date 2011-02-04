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
    FORM_PARAM_CONTENT = '_content'

    """The name to use for the content-type override field in the POST form."""
    FORM_PARAM_CONTENTTYPE = '_contenttype'

    def determine_content(self, request):
        """If the request contains content return a tuple of (content_type, content) otherwise return None.
        Note that content_type may be None if it is unset."""
        if not request.META.get('CONTENT_LENGTH', None) and not request.META.get('TRANSFER_ENCODING', None):
            return None
        
        content_type = request.META.get('CONTENT_TYPE', None)

        if (request.method == 'POST' and self.FORM_PARAM_CONTENT and
            request.POST.get(self.FORM_PARAM_CONTENT, None) is not None):

            # Set content type if form contains a none empty FORM_PARAM_CONTENTTYPE field
            content_type = None
            if self.FORM_PARAM_CONTENTTYPE and request.POST.get(self.FORM_PARAM_CONTENTTYPE, None):
                content_type = request.POST.get(self.FORM_PARAM_CONTENTTYPE, None)

            return (content_type, request.POST[self.FORM_PARAM_CONTENT])

        return (content_type, request.raw_post_data)