from django.core.urlresolvers import set_script_prefix
from django.views.decorators.csrf import csrf_exempt

from djangorestframework.compat import View
from djangorestframework.emitters import EmitterMixin
from djangorestframework.parsers import ParserMixin
from djangorestframework.authenticators import AuthenticatorMixin
from djangorestframework.validators import FormValidatorMixin
from djangorestframework.content import OverloadedContentMixin
from djangorestframework.methods import OverloadedPOSTMethodMixin 
from djangorestframework.response import Response, ResponseException
from djangorestframework import emitters, parsers, authenticators, status

import re

# TODO: Figure how out references and named urls need to work nicely
# TODO: POST on existing 404 URL, PUT on existing 404 URL
#
# NEXT: Exceptions on func() -> 500, tracebacks emitted if settings.DEBUG
#

__all__ = ['Resource']




class Resource(EmitterMixin, ParserMixin, AuthenticatorMixin, FormValidatorMixin,
               OverloadedContentMixin, OverloadedPOSTMethodMixin, View):
    """Handles incoming requests and maps them to REST operations,
    performing authentication, input deserialization, input validation, output serialization."""

    # List of RESTful operations which may be performed on this resource.
    allowed_methods = ('GET',)
    anon_allowed_methods = ()

    # List of emitters the resource can serialize the response with, ordered by preference
    emitters = ( emitters.JSONEmitter,
                 emitters.DocumentingHTMLEmitter,
                 emitters.DocumentingXHTMLEmitter,
                 emitters.DocumentingPlainTextEmitter,
                 emitters.XMLEmitter )

    # List of content-types the resource can read from
    parsers = ( parsers.JSONParser,
                parsers.XMLParser,
                parsers.FormParser,
                parsers.MultipartParser )
    
    # List of all authenticating methods to attempt
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


    # Some reserved parameters to allow us to use standard HTML forms with our resource
    # Override any/all of these with None to disable them, or override them with another value to rename them.
    CSRF_PARAM = 'csrfmiddlewaretoken'    # Django's CSRF token used in form params


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

        # These sets are determined now so that overridding classes can modify the various parameter names,
        # or set them to None to disable them. 
        self.RESERVED_FORM_PARAMS = set((self.METHOD_PARAM, self.CONTENTTYPE_PARAM, self.CONTENT_PARAM, self.CSRF_PARAM))
        self.RESERVED_QUERY_PARAMS = set((self.ACCEPT_QUERY_PARAM))
        self.RESERVED_FORM_PARAMS.discard(None)
        self.RESERVED_QUERY_PARAMS.discard(None)
        
        method = self.determine_method(request)

        try:

            # Authenticate the request, and store any context so that the resource operations can
            # do more fine grained authentication if required.
            #
            # Typically the context will be a user, or None if this is an anonymous request,
            # but it could potentially be more complex (eg the context of a request key which
            # has been signed against a particular set of permissions)
            auth_context = self.authenticate(request)

            # Ensure the requested operation is permitted on this resource
            self.check_method_allowed(method, auth_context)

            # Get the appropriate create/read/update/delete function
            func = getattr(self, self.callmap.get(method, None))
    
            # Either generate the response data, deserializing and validating any request data
            # TODO: Add support for message bodys on other HTTP methods, as it is valid (although non-conventional).
            if method in ('PUT', 'POST'):
                (content_type, content) = self.determine_content(request)
                parser_content = self.parse(content_type, content)
                cleaned_content = self.validate(parser_content)
                response_obj = func(request, auth_context, cleaned_content, *args, **kwargs)

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

        # Always add these headers
        response.headers['Allow'] = ', '.join(self.allowed_methods)
        response.headers['Vary'] = 'Authenticate, Allow'

        return self.emit(response)

