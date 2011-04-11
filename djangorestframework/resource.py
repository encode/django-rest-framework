from django.core.urlresolvers import set_script_prefix
from django.views.decorators.csrf import csrf_exempt

from djangorestframework.compat import View
from djangorestframework.emitters import EmitterMixin
from djangorestframework.authenticators import AuthenticatorMixin
from djangorestframework.validators import FormValidatorMixin
from djangorestframework.response import Response, ResponseException
from djangorestframework.request import RequestMixin
from djangorestframework import emitters, parsers, authenticators, status


# TODO: Figure how out references and named urls need to work nicely
# TODO: POST on existing 404 URL, PUT on existing 404 URL
#
# NEXT: Exceptions on func() -> 500, tracebacks emitted if settings.DEBUG

__all__ = ['Resource']


class Resource(EmitterMixin, AuthenticatorMixin, FormValidatorMixin, RequestMixin, View):
    """Handles incoming requests and maps them to REST operations,
    performing authentication, input deserialization, input validation, output serialization."""

    # List of RESTful operations which may be performed on this resource.
    # These are going to get dropped at some point, the allowable methods will be defined simply by
    # which methods are present on the request (in the same way as Django's generic View)
    allowed_methods = ('GET',)
    anon_allowed_methods = ()

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
    
    # List of all authenticating methods to attempt.
    authenticators = ( authenticators.UserLoggedInAuthenticator,
                       authenticators.BasicAuthenticator )

    # Optional form for input validation and presentation of HTML formatted responses.
    form = None

    # Allow name and description for the Resource to be set explicitly,
    # overiding the default classname/docstring behaviour.
    # These are used for documentation in the standard html and text emitters.
    name = None
    description = None

    # Map standard HTTP methods to function calls
    callmap = { 'GET': 'get', 'POST': 'post', 
                'PUT': 'put', 'DELETE': 'delete' }

    def get(self, request, auth, *args, **kwargs):
        """Must be subclassed to be implemented."""
        self.not_implemented('GET')


    def post(self, request, auth, content, *args, **kwargs):
        """Must be subclassed to be implemented."""
        self.not_implemented('POST')


    def put(self, request, auth, content, *args, **kwargs):
        """Must be subclassed to be implemented."""
        self.not_implemented('PUT')


    def delete(self, request, auth, *args, **kwargs):
        """Must be subclassed to be implemented."""
        self.not_implemented('DELETE')


    def not_implemented(self, operation):
        """Return an HTTP 500 server error if an operation is called which has been allowed by
        allowed_methods, but which has not been implemented."""
        raise ResponseException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                {'detail': '%s operation on this resource has not been implemented' % (operation, )})


    def check_method_allowed(self, method, auth):
        """Ensure the request method is permitted for this resource, raising a ResourceException if it is not."""

        if not method in self.callmap.keys():
            raise ResponseException(status.HTTP_501_NOT_IMPLEMENTED,
                                    {'detail': 'Unknown or unsupported method \'%s\'' % method})

        if not method in self.allowed_methods:
            raise ResponseException(status.HTTP_405_METHOD_NOT_ALLOWED,
                                    {'detail': 'Method \'%s\' not allowed on this resource.' % method})

        if auth is None and not method in self.anon_allowed_methods:
            raise ResponseException(status.HTTP_403_FORBIDDEN,
                                    {'detail': 'You do not have permission to access this resource. ' +
                                     'You may need to login or otherwise authenticate the request.'})


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

        self.request = request

        # Calls to 'reverse' will not be fully qualified unless we set the scheme/host/port here.
        prefix = '%s://%s' % (request.is_secure() and 'https' or 'http', request.get_host())
        set_script_prefix(prefix)

        try:
            # Authenticate the request, and store any context so that the resource operations can
            # do more fine grained authentication if required.
            #
            # Typically the context will be a user, or None if this is an anonymous request,
            # but it could potentially be more complex (eg the context of a request key which
            # has been signed against a particular set of permissions)
            auth_context = self.authenticate(request)

            # If using a form POST with '_method'/'_content'/'_content_type' overrides, then alter
            # self.method, self.content_type, self.CONTENT appropriately.
            self.perform_form_overloading()

            # Ensure the requested operation is permitted on this resource
            self.check_method_allowed(self.method, auth_context)

            # Get the appropriate create/read/update/delete function
            func = getattr(self, self.callmap.get(self.method, None))
    
            # Either generate the response data, deserializing and validating any request data
            # TODO: This is going to change to: func(request, *args, **kwargs)
            # That'll work out now that we have the lazily evaluated self.CONTENT property.
            if self.method in ('PUT', 'POST'):
                response_obj = func(request, auth_context, self.CONTENT, *args, **kwargs)

            else:
                response_obj = func(request, auth_context, *args, **kwargs)

            # Allow return value to be either Response, or an object, or None
            if isinstance(response_obj, Response):
                response = response_obj
            elif response_obj is not None:
                response = Response(status.HTTP_200_OK, response_obj)
            else:
                response = Response(status.HTTP_204_NO_CONTENT)

            # Pre-serialize filtering (eg filter complex objects into natively serializable types)
            response.cleaned_content = self.cleanup_response(response.raw_content)

        except ResponseException, exc:
            response = exc.response

        # Always add these headers.
        #
        # TODO - this isn't actually the correct way to set the vary header,
        # also it's currently sub-obtimal for HTTP caching - need to sort that out. 
        response.headers['Allow'] = ', '.join(self.allowed_methods)
        response.headers['Vary'] = 'Authenticate, Accept'

        return self.emit(response)

