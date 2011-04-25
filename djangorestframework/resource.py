from django.core.urlresolvers import set_script_prefix
from django.views.decorators.csrf import csrf_exempt

from djangorestframework.compat import View
from djangorestframework.response import Response, ErrorResponse
from djangorestframework.mixins import RequestMixin, ResponseMixin, AuthMixin
from djangorestframework import emitters, parsers, authenticators, permissions, validators, status


# TODO: Figure how out references and named urls need to work nicely
# TODO: POST on existing 404 URL, PUT on existing 404 URL
#
# NEXT: Exceptions on func() -> 500, tracebacks emitted if settings.DEBUG

__all__ = ['Resource']


class Resource(RequestMixin, ResponseMixin, AuthMixin, View):
    """Handles incoming requests and maps them to REST operations,
    performing authentication, input deserialization, input validation, output serialization."""

    http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace', 'patch']

    # List of emitters the resource can serialize the response with, ordered by preference.
    emitters = ( emitters.JSONEmitter,
                 emitters.DocumentingHTMLEmitter,
                 emitters.DocumentingXHTMLEmitter,
                 emitters.DocumentingPlainTextEmitter,
                 emitters.XMLEmitter )

    # List of parsers the resource can parse the request with.
    parsers = ( parsers.JSONParser,
                parsers.FormParser,
                parsers.MultipartParser )

    # List of validators to validate, cleanup and normalize the request content    
    validators = ( validators.FormValidator, )

    # List of all authenticating methods to attempt.
    authenticators = ( authenticators.UserLoggedInAuthenticator,
                       authenticators.BasicAuthenticator )
    
    # List of all permissions required to access the resource
    permissions = ( permissions.DeleteMePermission, )

    # Optional form for input validation and presentation of HTML formatted responses.
    form = None

    # Allow name and description for the Resource to be set explicitly,
    # overiding the default classname/docstring behaviour.
    # These are used for documentation in the standard html and text emitters.
    name = None
    description = None

    @property
    def allowed_methods(self):
        return [method.upper() for method in self.http_method_names if hasattr(self, method)]

    def http_method_not_allowed(self, request, *args, **kwargs):
        """Return an HTTP 405 error if an operation is called which does not have a handler method."""
        raise ErrorResponse(status.HTTP_405_METHOD_NOT_ALLOWED,
                                {'detail': 'Method \'%s\' not allowed on this resource.' % self.method})


    def cleanup_response(self, data):
        """Perform any resource-specific data filtering prior to the standard HTTP
        content-type serialization.

        Eg filter complex objects that cannot be serialized by json/xml/etc into basic objects that can.
        
        TODO: This is going to be removed.  I think that the 'fields' behaviour is going to move into
        the EmitterMixin and Emitter classes."""
        return data


    # Session based authentication is explicitly CSRF validated, all other authentication is CSRF exempt.
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        """This method is the core of Resource, through which all requests are passed.

        Broadly this consists of the following procedure:

        0. ensure the operation is permitted
        1. deserialize request content into request data, using standard HTTP content types (PUT/POST only)
        2. cleanup and validate request data (PUT/POST only)
        3. call the core method to get the response data
        4. cleanup the response data
        5. serialize response data into response content, using standard HTTP content negotiation
        """
        try:
            self.request = request
            self.args = args
            self.kwargs = kwargs
    
            # Calls to 'reverse' will not be fully qualified unless we set the scheme/host/port here.
            prefix = '%s://%s' % (request.is_secure() and 'https' or 'http', request.get_host())
            set_script_prefix(prefix)
    
            try:
                # If using a form POST with '_method'/'_content'/'_content_type' overrides, then alter
                # self.method, self.content_type, self.RAW_CONTENT & self.CONTENT appropriately.
                self.perform_form_overloading()
    
                # Authenticate and check request is has the relevant permissions
                self.check_permissions()
    
                # Get the appropriate handler method
                if self.method.lower() in self.http_method_names:
                    handler = getattr(self, self.method.lower(), self.http_method_not_allowed)
                else:
                    handler = self.http_method_not_allowed
    
                response_obj = handler(request, *args, **kwargs)
    
                # Allow return value to be either Response, or an object, or None
                if isinstance(response_obj, Response):
                    response = response_obj
                elif response_obj is not None:
                    response = Response(status.HTTP_200_OK, response_obj)
                else:
                    response = Response(status.HTTP_204_NO_CONTENT)
    
                # Pre-serialize filtering (eg filter complex objects into natively serializable types)
                response.cleaned_content = self.cleanup_response(response.raw_content)
    
            except ErrorResponse, exc:
                response = exc.response
    
            # Always add these headers.
            #
            # TODO - this isn't actually the correct way to set the vary header,
            # also it's currently sub-obtimal for HTTP caching - need to sort that out. 
            response.headers['Allow'] = ', '.join(self.allowed_methods)
            response.headers['Vary'] = 'Authenticate, Accept'
    
            return self.emit(response)
        except:
            import traceback
            traceback.print_exc()

