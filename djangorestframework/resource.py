from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from djangorestframework.parsers import ParserMixin
from djangorestframework.validators import FormValidatorMixin
from djangorestframework.content import OverloadedContentMixin
from djangorestframework.methods import OverloadedPOSTMethodMixin 
from djangorestframework import emitters, parsers, authenticators
from djangorestframework.response import status, Response, ResponseException

from decimal import Decimal
import re

# TODO: Figure how out references and named urls need to work nicely
# TODO: POST on existing 404 URL, PUT on existing 404 URL
#
# NEXT: Exceptions on func() -> 500, tracebacks emitted if settings.DEBUG
#

__all__ = ['Resource']


_MSIE_USER_AGENT = re.compile(r'^Mozilla/[0-9]+\.[0-9]+ \([^)]*; MSIE [0-9]+\.[0-9]+[a-z]?;[^)]*\)(?!.* Opera )')


class Resource(ParserMixin, FormValidatorMixin, OverloadedContentMixin, OverloadedPOSTMethodMixin):
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
                parsers.FormParser )
    
    # List of all authenticating methods to attempt
    authenticators = ( authenticators.UserLoggedInAuthenticator,
                       authenticators.BasicAuthenticator )

    # Optional form for input validation and presentation of HTML formatted responses.
    form = None

    # Map standard HTTP methods to function calls
    callmap = { 'GET': 'get', 'POST': 'post', 
                'PUT': 'put', 'DELETE': 'delete' }

    # Some reserved parameters to allow us to use standard HTML forms with our resource
    # Override any/all of these with None to disable them, or override them with another value to rename them.
    ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params    CONTENTTYPE_PARAM = '_contenttype'    # Allow override of Content-Type header in form params (allows sending arbitrary content with standard forms)
    CSRF_PARAM = 'csrfmiddlewaretoken'    # Django's CSRF token used in form params

    _MUNGE_IE_ACCEPT_HEADER = True

    def __new__(cls, *args, **kwargs):
        """Make the class callable so it can be used as a Django view."""
        self = object.__new__(cls)
        if args:
            request = args[0]
            self.__init__(request)
            return self._handle_request(request, *args[1:], **kwargs)
        else:
            self.__init__()
            return self


    def __init__(self, request=None):
        """"""
        # Setup the resource context
        self.request = request
        self.response = None
        self.form_instance = None

        # These sets are determined now so that overridding classes can modify the various parameter names,
        # or set them to None to disable them. 
        self.RESERVED_FORM_PARAMS = set((self.METHOD_PARAM, self.CONTENTTYPE_PARAM, self.CONTENT_PARAM, self.CSRF_PARAM))
        self.RESERVED_QUERY_PARAMS = set((self.ACCEPT_QUERY_PARAM))
        self.RESERVED_FORM_PARAMS.discard(None)
        self.RESERVED_QUERY_PARAMS.discard(None)


    @property
    def name(self):
        """Provide a name for the resource.
        By default this is the class name, with 'CamelCaseNames' converted to 'Camel Case Names'."""
        class_name = self.__class__.__name__
        return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name).strip()

    @property
    def description(self):
        """Provide a description for the resource.
        By default this is the class's docstring with leading line spaces stripped."""
        return re.sub(re.compile('^ +', re.MULTILINE), '', self.__doc__)

    @property
    def emitted_media_types(self):
        """Return an list of all the media types that this resource can emit."""
        return [emitter.media_type for emitter in self.emitters]

    @property
    def default_emitter(self):
        """Return the resource's most prefered emitter.
        (This emitter is used if the client does not send and Accept: header, or sends Accept: */*)"""
        return self.emitters[0]

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


    def reverse(self, view, *args, **kwargs):
        """Return a fully qualified URI for a given view or resource.
        Add the domain using the Sites framework if possible, otherwise fallback to using the current request."""
        return self.add_domain(reverse(view, args=args, kwargs=kwargs))


    def not_implemented(self, operation):
        """Return an HTTP 500 server error if an operation is called which has been allowed by
        allowed_methods, but which has not been implemented."""
        raise ResponseException(status.HTTP_500_INTERNAL_SERVER_ERROR,
                                {'detail': '%s operation on this resource has not been implemented' % (operation, )})


    def add_domain(self, path):
        """Given a path, return an fully qualified URI.
        Use the Sites framework if possible, otherwise fallback to using the domain from the current request."""

        # Note that out-of-the-box the Sites framework uses the reserved domain 'example.com'
        # See RFC 2606 - http://www.faqs.org/rfcs/rfc2606.html
        try:
            site = Site.objects.get_current()
            if site.domain and site.domain != 'example.com':
                return 'http://%s%s' % (site.domain, path)
        except:
            pass

        return self.request.build_absolute_uri(path)


    def authenticate(self, request):
        """Attempt to authenticate the request, returning an authentication context or None.
        An authentication context may be any object, although in many cases it will be a User instance."""
        
        # Attempt authentication against each authenticator in turn,
        # and return None if no authenticators succeed in authenticating the request.
        for authenticator in self.authenticators:
            auth_context = authenticator(self).authenticate(request)
            if auth_context:
                return auth_context

        return None


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

        Eg filter complex objects that cannot be serialized by json/xml/etc into basic objects that can."""
        return data


    def determine_emitter(self, request):
        """Return the appropriate emitter for the output, given the client's 'Accept' header,
        and the content types that this Resource knows how to serve.
        
        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html"""

        if self.ACCEPT_QUERY_PARAM and request.GET.get(self.ACCEPT_QUERY_PARAM, None):
            # Use _accept parameter override
            accept_list = [request.GET.get(self.ACCEPT_QUERY_PARAM)]
        elif self._MUNGE_IE_ACCEPT_HEADER and request.META.has_key('HTTP_USER_AGENT') and _MSIE_USER_AGENT.match(request.META['HTTP_USER_AGENT']):
            accept_list = ['text/html', '*/*']
        elif request.META.has_key('HTTP_ACCEPT'):
            # Use standard HTTP Accept negotiation
            accept_list = request.META["HTTP_ACCEPT"].split(',')
        else:
            # No accept header specified
            return self.default_emitter
        
        # Parse the accept header into a dict of {qvalue: set of media types}
        # We ignore mietype parameters
        accept_dict = {}    
        for token in accept_list:
            components = token.split(';')
            mimetype = components[0].strip()
            qvalue = Decimal('1.0')
            
            if len(components) > 1:
                # Parse items that have a qvalue eg text/html;q=0.9
                try:
                    (q, num) = components[-1].split('=')
                    if q == 'q':
                        qvalue = Decimal(num)
                except:
                    # Skip malformed entries
                    continue

            if accept_dict.has_key(qvalue):
                accept_dict[qvalue].add(mimetype)
            else:
                accept_dict[qvalue] = set((mimetype,))
        
        # Convert to a list of sets ordered by qvalue (highest first)
        accept_sets = [accept_dict[qvalue] for qvalue in sorted(accept_dict.keys(), reverse=True)]
       
        for accept_set in accept_sets:
            # Return any exact match
            for emitter in self.emitters:
                if emitter.media_type in accept_set:
                    return emitter

            # Return any subtype match
            for emitter in self.emitters:
                if emitter.media_type.split('/')[0] + '/*' in accept_set:
                    return emitter

            # Return default
            if '*/*' in accept_set:
                return self.default_emitter
      

        raise ResponseException(status.HTTP_406_NOT_ACCEPTABLE,
                                {'detail': 'Could not statisfy the client\'s Accept header',
                                 'available_types': self.emitted_media_types})


    def _handle_request(self, request, *args, **kwargs):
        """This method is the core of Resource, through which all requests are passed.

        Broadly this consists of the following procedure:

        0. ensure the operation is permitted
        1. deserialize request content into request data, using standard HTTP content types (PUT/POST only)
        2. cleanup and validate request data (PUT/POST only)
        3. call the core method to get the response data
        4. cleanup the response data
        5. serialize response data into response content, using standard HTTP content negotiation
        """
        emitter = None
        method = self.determine_method(request)

        try:
            # Before we attempt anything else determine what format to emit our response data with.
            emitter = self.determine_emitter(request)

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
            # TODO: Add support for message bodys on other HTTP methods, as it is valid.
            if method in ('PUT', 'POST'):
                (content_type, content) = self.determine_content(request)
                parser_content = self.parse(content_type, content)
                cleaned_content = self.validate(parser_content)
                response = func(request, auth_context, cleaned_content, *args, **kwargs)

            else:
                response = func(request, auth_context, *args, **kwargs)

            # Allow return value to be either Response, or an object, or None
            if isinstance(response, Response):
                self.response = response
            elif response is not None:
                self.response = Response(status.HTTP_200_OK, response)
            else:
                self.response = Response(status.HTTP_204_NO_CONTENT)

            # Pre-serialize filtering (eg filter complex objects into natively serializable types)
            self.response.cleaned_content = self.cleanup_response(self.response.raw_content)


        except ResponseException, exc:
            self.response = exc.response

            # Fall back to the default emitter if we failed to perform content negotiation
            if emitter is None:
                emitter = self.default_emitter


        # Always add these headers
        self.response.headers['Allow'] = ', '.join(self.allowed_methods)
        self.response.headers['Vary'] = 'Authenticate, Allow'

        # Serialize the response content
        if self.response.has_content_body:
            content = emitter(self).emit(output=self.response.cleaned_content)
        else:
            content = emitter(self).emit()

        # Build the HTTP Response
        # TODO: Check if emitter.mimetype is underspecified, or if a content-type header has been set
        resp = HttpResponse(content, mimetype=emitter.media_type, status=self.response.status)
        for (key, val) in self.response.headers.items():
            resp[key] = val

        return resp

