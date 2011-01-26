from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from flywheel import emitters, parsers, authenticators
from flywheel.response import status, Response, ResponseException

from decimal import Decimal
import re
from itertools import chain

# TODO: Display user login in top panel: http://stackoverflow.com/questions/806835/django-redirect-to-previous-page-after-login
# TODO: Figure how out references and named urls need to work nicely
# TODO: POST on existing 404 URL, PUT on existing 404 URL
# TODO: Remove is_error throughout
#
# NEXT: Exceptions on func() -> 500, tracebacks emitted if settings.DEBUG
# NEXT: Generic content form
# NEXT: Remove self.blah munging  (Add a ResponseContext object?)
# NEXT: Caching cleverness
# NEXT: Test non-existent fields on ModelResources
#
# FUTURE: Erroring on read-only fields

# Documentation, Release

__all__ = ['Resource']



class Resource(object):
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
    ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params
    METHOD_PARAM = '_method'              # Allow POST overloading in form params
    CONTENTTYPE_PARAM = '_contenttype'    # Allow override of Content-Type header in form params (allows sending arbitrary content with standard forms)
    CONTENT_PARAM = '_content'            # Allow override of body content in form params (allows sending arbitrary content with standard forms) 
    CSRF_PARAM = 'csrfmiddlewaretoken'    # Django's CSRF token used in form params


    def __new__(cls, request, *args, **kwargs):
        """Make the class callable so it can be used as a Django view."""
        self = object.__new__(cls)
        self.__init__(request)
        # TODO: Remove this debugging code
        try:
            return self._handle_request(request, *args, **kwargs)
        except:
            import traceback
            traceback.print_exc()
            raise


    def __init__(self, request):
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

    @property
    def parsed_media_types(self):
        """Return an list of all the media types that this resource can emit."""
        return [parser.media_type for parser in self.parsers]
    
    @property
    def default_parser(self):
        """Return the resource's most prefered emitter.
        (This has no behavioural effect, but is may be used by documenting emitters)"""        
        return self.parsers[0]


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
    
    
    def determine_method(self, request):
        """Determine the HTTP method that this request should be treated as.
        Allows PUT and DELETE tunneling via the _method parameter if METHOD_PARAM is set."""
        method = request.method.upper()

        if method == 'POST' and self.METHOD_PARAM and request.POST.has_key(self.METHOD_PARAM):
            method = request.POST[self.METHOD_PARAM].upper()
        
        return method


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

    def get_form(self, data=None):
        """Optionally return a Django Form instance, which may be used for validation
        and/or rendered by an HTML/XHTML emitter.
        
        If data is not None the form will be bound to data."""

        if self.form:
            if data:
                return self.form(data)
            else:
                return self.form()
        return None
  
  
    def cleanup_request(self, data, form_instance):
        """Perform any resource-specific data deserialization and/or validation
        after the initial HTTP content-type deserialization has taken place.
        
        Returns a tuple containing the cleaned up data, and optionally a form bound to that data.
        
        By default this uses form validation to filter the basic input into the required types."""

        if form_instance is None:
            return data
        
        # Default form validation does not check for additional invalid fields
        non_existent_fields = []
        for key in set(data.keys()) - set(form_instance.fields.keys()):
            non_existent_fields.append(key)

        if not form_instance.is_valid() or non_existent_fields:
            if not form_instance.errors and not non_existent_fields:
                # If no data was supplied the errors property will be None
                details = 'No content was supplied'
                
            else:
                # Add standard field errors
                details = dict((key, map(unicode, val)) for (key, val) in form_instance.errors.iteritems() if key != '__all__')

                # Add any non-field errors
                if form_instance.non_field_errors():
                    details['errors'] = form_instance.non_field_errors()

                # Add any non-existent field errors
                for key in non_existent_fields:
                    details[key] = ['This field does not exist']

            # Bail.  Note that we will still serialize this response with the appropriate content type 
            raise ResponseException(status.HTTP_400_BAD_REQUEST, {'detail': details})

        return form_instance.cleaned_data


    def cleanup_response(self, data):
        """Perform any resource-specific data filtering prior to the standard HTTP
        content-type serialization.

        Eg filter complex objects that cannot be serialized by json/xml/etc into basic objects that can."""
        return data


    def determine_parser(self, request):
        """Return the appropriate parser for the input, given the client's 'Content-Type' header,
        and the content types that this Resource knows how to parse."""
        content_type = request.META.get('CONTENT_TYPE', 'application/x-www-form-urlencoded')
        raw_content = request.raw_post_data
    
        split = content_type.split(';', 1)
        if len(split) > 1:
            content_type = split[0]
        content_type = content_type.strip()
        
        # If CONTENTTYPE_PARAM is turned on, and this is a standard POST form then allow the content type to be overridden
        if (content_type == 'application/x-www-form-urlencoded' and
            request.method == 'POST' and
            self.CONTENTTYPE_PARAM and
            self.CONTENT_PARAM and
            request.POST.get(self.CONTENTTYPE_PARAM, None) and
            request.POST.get(self.CONTENT_PARAM, None)):
            raw_content = request.POST[self.CONTENT_PARAM]
            content_type = request.POST[self.CONTENTTYPE_PARAM]

        # Create a list of list of (media_type, Parser) tuples
        media_type_to_parser = dict([(parser.media_type, parser) for parser in self.parsers])

        try:
            return (media_type_to_parser[content_type], raw_content)
        except KeyError:
            raise ResponseException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                    {'detail': 'Unsupported media type \'%s\'' % content_type})


    def determine_emitter(self, request):
        """Return the appropriate emitter for the output, given the client's 'Accept' header,
        and the content types that this Resource knows how to serve.
        
        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html"""

        if self.ACCEPT_QUERY_PARAM and request.GET.get(self.ACCEPT_QUERY_PARAM, None):
            # Use _accept parameter override
            accept_list = [request.GET.get(self.ACCEPT_QUERY_PARAM)]
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
                (parser, raw_content) = self.determine_parser(request)
                data = parser(self).parse(raw_content)
                self.form_instance = self.get_form(data)
                data = self.cleanup_request(data, self.form_instance)
                response = func(request, auth_context, data, *args, **kwargs)

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

