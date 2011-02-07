"""Mixin classes that provide a determine_method(request) function to determine the HTTP
method that a given request should be treated as.  We use this more generic behaviour to
allow for overloaded methods in POST forms.

See Richardson & Ruby's RESTful Web Services for justification.
"""

class MethodMixin(object):
    """Base class for all MethodMixin classes, which simply defines the interface they provide."""
    def determine_method(self, request):
        """Simply return GET, POST etc... as appropriate."""
        raise NotImplementedError()

   
class StandardMethodMixin(MethodMixin):
    """Provide for standard HTTP behaviour, with no overloaded POST."""

    def determine_method(self, request):
        """Simply return GET, POST etc... as appropriate."""
        return request.method.upper()


class OverloadedPOSTMethodMixin(MethodMixin):
    """Provide for overloaded POST behaviour."""

    """The name to use for the method override field in the POST form."""
    METHOD_PARAM = '_method'

    def determine_method(self, request):
        """Simply return GET, POST etc... as appropriate, allowing for POST overloading
        by setting a form field with the requested method name."""
        method = request.method.upper()
        if method == 'POST' and self.METHOD_PARAM and request.POST.has_key(self.METHOD_PARAM):
            method = request.POST[self.METHOD_PARAM].upper()
        return method