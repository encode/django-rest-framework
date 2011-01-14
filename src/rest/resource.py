from django.http import HttpResponse
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.core.handlers.wsgi import STATUS_CODE_TEXT
from rest import emitters, parsers
from decimal import Decimal
import re

# TODO: Display user login in top panel: http://stackoverflow.com/questions/806835/django-redirect-to-previous-page-after-login
# TODO: Return basic object, not tuple
# TODO: Take request, not headers
# TODO: Remove self.blah munging  (Add a ResponseContext object)
# TODO: Erroring on non-existent fields
# TODO: Standard exception classes and module for status codes
# TODO: Figure how out references and named urls need to work nicely
# TODO: POST on existing 404 URL, PUT on existing 404 URL
# TODO: Authentication
#
# FUTURE: Erroring on read-only fields

# Documentation, Release

# 
STATUS_400_BAD_REQUEST = 400
STATUS_405_METHOD_NOT_ALLOWED = 405
STATUS_406_NOT_ACCEPTABLE = 406
STATUS_415_UNSUPPORTED_MEDIA_TYPE = 415
STATUS_500_INTERNAL_SERVER_ERROR = 500
STATUS_501_NOT_IMPLEMENTED = 501


class ResourceException(Exception):
    def __init__(self, status, content='', headers={}):
        self.status = status
        self.content = content
        self.headers = headers


class Resource(object):
    # List of RESTful operations which may be performed on this resource.
    allowed_operations = ('read',)
    anon_allowed_operations = ()

    # Optional form for input validation and presentation of HTML formatted responses. 
    form = None

    # List of content-types the resource can respond with, ordered by preference
    emitters = ( ('application/json', emitters.JSONEmitter),
                 ('text/html', emitters.HTMLEmitter),
                 ('application/xhtml+xml', emitters.HTMLEmitter),
                 ('text/plain', emitters.TextEmitter),
                 ('application/xml', emitters.XMLEmitter), )

    # List of content-types the resource can read from
    parsers = { 'application/json': parsers.JSONParser,
                'application/xml': parsers.XMLParser,
                'application/x-www-form-urlencoded': parsers.FormParser,
                'multipart/form-data': parsers.FormParser }

    # Map standard HTTP methods to RESTful operations
    CALLMAP = { 'GET': 'read', 'POST': 'create', 
                'PUT': 'update', 'DELETE': 'delete' }

    REVERSE_CALLMAP = dict([(val, key) for (key, val) in CALLMAP.items()])

    # Some reserved parameters to allow us to use standard HTML forms with our resource
    METHOD_PARAM = '_method'              # Allow POST overloading
    ACCEPT_PARAM = '_accept'              # Allow override of Accept header in GET requests
    CONTENTTYPE_PARAM = '_contenttype'    # Allow override of Content-Type header (allows sending arbitrary content with standard forms)
    CONTENT_PARAM = '_content'            # Allow override of body content (allows sending arbitrary content with standard forms) 
    CSRF_PARAM = 'csrfmiddlewaretoken'    # Django's CSRF token

    RESERVED_PARAMS = set((METHOD_PARAM, ACCEPT_PARAM, CONTENTTYPE_PARAM, CONTENT_PARAM, CSRF_PARAM))


    def __new__(cls, request, *args, **kwargs):
        """Make the class callable so it can be used as a Django view."""
        self = object.__new__(cls)
        self.__init__()
        return self._handle_request(request, *args, **kwargs)


    def __init__(self):
        pass


    def name(self):
        """Provide a name for the resource.
        By default this is the class name, with 'CamelCaseNames' converted to 'Camel Case Names'."""
        class_name = self.__class__.__name__
        return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name).strip()


    def description(self):
        """Provide a description for the resource.
        By default this is the class's docstring with leading line spaces stripped."""
        return re.sub(re.compile('^ +', re.MULTILINE), '', self.__doc__)
   

    def available_content_types(self):
        """Return a list of strings of all the content-types that this resource can emit."""
        return [item[0] for item in self.emitters]


    def resp_status_text(self):
        """Return reason text corrosponding to our HTTP response status code.
        Provided for convienience."""
        return STATUS_CODE_TEXT.get(self.resp_status, '')


    def reverse(self, view, *args, **kwargs):
        """Return a fully qualified URI for a given view or resource.
        Use the Sites framework if possible, otherwise fallback to using the current request."""
        return self.add_domain(reverse(view, *args, **kwargs))


    def add_domain(self, path):
        """Given a path, return an fully qualified URI.
        Use the Sites framework if possible, otherwise fallback to using the domain from the current request."""
        try:
            site = Site.objects.get_current()
            if site.domain and site.domain != 'example.com':
                return 'http://%s%s' % (site.domain, path)
        except:
            pass

        return self.request.build_absolute_uri(path)


    def read(self, headers={}, *args, **kwargs):
        """RESTful read on the resource, which must be subclassed to be implemented.  Should be a safe operation."""
        self.not_implemented('read')


    def create(self, data=None, headers={}, *args, **kwargs):
        """RESTful create on the resource, which must be subclassed to be implemented."""
        self.not_implemented('create')


    def update(self, data=None, headers={}, *args, **kwargs):
        """RESTful update on the resource, which must be subclassed to be implemented.  Should be an idempotent operation."""
        self.not_implemented('update')


    def delete(self, headers={}, *args, **kwargs):
        """RESTful delete on the resource, which must be subclassed to be implemented.  Should be an idempotent operation."""
        self.not_implemented('delete')


    def not_implemented(self, operation):
        """Return an HTTP 500 server error if an operation is called which has been allowed by
        allowed_operations, but which has not been implemented."""
        raise ResourceException(STATUS_500_INTERNAL_SERVER_ERROR,
                                {'detail': '%s operation on this resource has not been implemented' % (operation, )})


    def determine_method(self, request):
        """Determine the HTTP method that this request should be treated as.
        Allow for PUT and DELETE tunneling via the _method parameter."""
        method = request.method.upper()

        if method == 'POST' and self.METHOD_PARAM and request.POST.has_key(self.METHOD_PARAM):
            method = request.POST[self.METHOD_PARAM].upper()
        
        return method


    def authenticate(self):
        """TODO"""
        # user = ...
        # if DEBUG and request is from localhost
        # if anon_user and not anon_allowed_operations raise PermissionDenied
        # return 

    def check_method_allowed(self, method):
        """Ensure the request method is acceptable for this resource."""
        if not method in self.CALLMAP.keys():
            raise ResourceException(STATUS_501_NOT_IMPLEMENTED,
                                    {'detail': 'Unknown or unsupported method \'%s\'' % method})
            
        if not self.CALLMAP[method] in self.allowed_operations:
            raise ResourceException(STATUS_405_METHOD_NOT_ALLOWED,
                                    {'detail': 'Method \'%s\' not allowed on this resource.' % method})



    def get_bound_form(self, data=None, is_response=False):
        """Optionally return a Django Form instance, which may be used for validation
        and/or rendered by an HTML/XHTML emitter.
        
        If data is not None the form will be bound to data.  is_response indicates if data should be
        treated as the input data (bind to client input) or the response data (bind to an existing object)."""
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

        if not form_instance.is_valid():
            if not form_instance.errors:
                details = 'No content was supplied'
            else:
                details = dict((key, map(unicode, val)) for (key, val) in form_instance.errors.iteritems())
                if form_instance.non_field_errors():
                    details['_extra'] = self.form.non_field_errors()

            raise ResourceException(STATUS_400_BAD_REQUEST, {'detail': details})

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
        split = content_type.split(';', 1)
        if len(split) > 1:
            content_type = split[0]
        content_type = content_type.strip()

        try:
            return self.parsers[content_type]
        except KeyError:
            raise ResourceException(STATUS_415_UNSUPPORTED_MEDIA_TYPE,
                                    {'detail': 'Unsupported media type \'%s\'' % content_type})


    def determine_emitter(self, request):
        """Return the appropriate emitter for the output, given the client's 'Accept' header,
        and the content types that this Resource knows how to serve.
        
        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html"""
        default = self.emitters[0]

        if self.ACCEPT_PARAM and request.GET.get(self.ACCEPT_PARAM, None):
            # Use _accept parameter override
            accept_list = [(request.GET.get(self.ACCEPT_PARAM),)]
        elif request.META.has_key('HTTP_ACCEPT'):
            # Use standard HTTP Accept negotiation
            accept_list = [item.split(';') for item in request.META["HTTP_ACCEPT"].split(',')]
        else:
            # No accept header specified
            return default
        
        # Parse the accept header into a dict of {Priority: List of Mimetypes}
        accept_dict = {}    
        for item in accept_list:
            mimetype = item[0].strip()
            qvalue = Decimal('1.0')
            
            if len(item) > 1:
                # Parse items that have a qvalue eg text/html;q=0.9
                try:
                    (q, num) = item[1].split('=')
                    if q == 'q':
                        qvalue = Decimal(num)
                except:
                    # Skip malformed entries
                    continue

            if accept_dict.has_key(qvalue):
                accept_dict[qvalue].append(mimetype)
            else:
                accept_dict[qvalue] = [mimetype]
        
        # Go through all accepted mimetypes in priority order and return our first match
        qvalues = accept_dict.keys()
        qvalues.sort(reverse=True)
       
        for qvalue in qvalues:
            for (mimetype, emitter) in self.emitters:
                for accept_mimetype in accept_dict[qvalue]:
                    if ((accept_mimetype == '*/*') or
                        (accept_mimetype.endswith('/*') and mimetype.startswith(accept_mimetype[:-1])) or
                        (accept_mimetype == mimetype)):
                            return (mimetype, emitter)      

        raise ResourceException(STATUS_406_NOT_ACCEPTABLE,
                                {'detail': 'Could not statisfy the client\'s accepted content type',
                                 'accepted_types': [item[0] for item in self.emitters]})


    def _handle_request(self, request, *args, **kwargs):
        """
        
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

        # We make these attributes to allow for a certain amount of munging,
        # eg The HTML emitter needs to render this information
        self.request = request
        self.form_instance = None
        self.resp_status = None
        self.resp_headers = {}

        try:
            # Before we attempt anything else determine what format to emit our response data with.
            mimetype, emitter = self.determine_emitter(request)

            # Ensure the requested operation is permitted on this resource
            self.check_method_allowed(method)

            # Get the appropriate create/read/update/delete function
            func = getattr(self, self.CALLMAP.get(method, ''))
    
            # Either generate the response data, deserializing and validating any request data
            if method in ('PUT', 'POST'):
                parser = self.determine_parser(request)
                data = parser(self).parse(request.raw_post_data)
                self.form_instance = self.get_bound_form(data)
                data = self.cleanup_request(data, self.form_instance)
                (self.resp_status, ret, self.resp_headers) = func(data, request.META, *args, **kwargs)

            else:
                (self.resp_status, ret, self.resp_headers) = func(request.META, *args, **kwargs)
                if emitter.uses_forms:
                    self.form_instance = self.get_bound_form(ret, is_response=True)


        except ResourceException, exc:
            (self.resp_status, ret, self.resp_headers) = (exc.status, exc.content, exc.headers)
            if emitter is None:
                mimetype, emitter = self.emitters[0] 
            if self.form_instance is None and emitter.uses_forms:
                self.form_instance = self.get_bound_form()


        # Always add the allow header
        self.resp_headers['Allow'] = ', '.join([self.REVERSE_CALLMAP[operation] for operation in self.allowed_operations])
            
        # Serialize the response content
        ret = self.cleanup_response(ret)
        content = emitter(self).emit(ret)

        # Build the HTTP Response
        resp = HttpResponse(content, mimetype=mimetype, status=self.resp_status)
        for (key, val) in self.resp_headers.items():
            resp[key] = val

        return resp

