from django.http import HttpResponse
from django.core.urlresolvers import reverse
from rest import emitters, parsers, utils
from decimal import Decimal

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

    allowed_methods = ('GET',)

    callmap = { 'GET': 'read', 'POST': 'create', 
                'PUT': 'update', 'DELETE': 'delete' }

    emitters = [ ('application/json', emitters.JSONEmitter),
                 ('text/html', emitters.HTMLEmitter),
                 ('application/xhtml+xml', emitters.HTMLEmitter),
                 ('text/plain', emitters.TextEmitter),
                 ('application/xml', emitters.XMLEmitter), ]

    parsers = { 'application/json': parsers.JSONParser,
                'application/xml': parsers.XMLParser,
                'application/x-www-form-urlencoded': parsers.FormParser,
                'multipart/form-data': parsers.FormParser }

    create_form = None
    update_form = None

    METHOD_PARAM = '_method'
    ACCEPT_PARAM = '_accept'


    def __new__(cls, request, *args, **kwargs):
        self = object.__new__(cls)
        self.__init__()
        self._request = request
        return self._handle_request(request, *args, **kwargs)


    def __init__(self):
        pass


    def _determine_method(self, request):
        """Determine the HTTP method that this request should be treated as,
        allowing for PUT and DELETE tunneling via the _method parameter."""
        method = request.method
        
        if method == 'POST' and request.POST.has_key(self.METHOD_PARAM):
            method = request.POST[self.METHOD_PARAM].upper()
        
        return method


    def _check_method_allowed(self, method):
        if not method in self.allowed_methods:
            raise ResourceException(STATUS_405_METHOD_NOT_ALLOWED,
                                    {'detail': 'Method \'%s\' not allowed on this resource.' % method})
        
        if not method in self.callmap.keys():
            raise ResourceException(STATUS_501_NOT_IMPLEMENTED,
                                    {'detail': 'Unknown or unsupported method \'%s\'' % method})


    def _determine_parser(self, request):
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
                                    {'detail': 'Unsupported content type \'%s\'' % content_type})
    
    def _determine_emitter(self, request):
        """Return the appropriate emitter for the output, given the client's 'Accept' header,
        and the content types that this Resource knows how to serve.
        
        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
        """

        default = self.emitters[0]

        if not request.META.has_key('HTTP_ACCEPT'):
            return default
        
        # Parse the accept header into a dict of {Priority: List of Mimetypes}
        accept_list = [item.split(';') for item in request.META["HTTP_ACCEPT"].split(',')]
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

    
    def _validate_data(self, method, data):
        """If there is an appropriate form to deal with this operation,
        then validate the data and return the resulting dictionary.
        """
        if method == 'PUT' and self.update_form:
            form = self.update_form(data)
        elif method == 'POST' and self.create_form:
            form = self.create_form(data)
        else:
            return data

        if not form.is_valid():
            raise ResourceException(STATUS_400_BAD_REQUEST,
                                    {'detail': dict((k, map(unicode, v))
                                                    for (k,v) in form.errors.iteritems())})

        return form.cleaned_data


    def _handle_request(self, request, *args, **kwargs):

        # Hack to ensure PUT requests get the same form treatment as POST requests
        utils.coerce_put_post(request)

        # Get the request method, allowing for PUT and DELETE tunneling
        method = self._determine_method(request)

        try:
            self._check_method_allowed(method)
    
            # Parse the HTTP Request content
            func = getattr(self, self.callmap.get(method, ''))
    
            if method in ('PUT', 'POST'):
                parser = self._determine_parser(request)
                data = parser(self, request).parse(request.raw_post_data)
                data = self._validate_data(method, data)
                (status, ret, headers) = func(data, request.META, *args, **kwargs)

            else:
                (status, ret, headers) = func(request.META, *args, **kwargs)
        except ResourceException, exc:
            (status, ret, headers) = (exc.status, exc.content, exc.headers)

        headers['Allow'] = ', '.join(self.allowed_methods)
        
        # Serialize the HTTP Response content
        try:        
            mimetype, emitter = self._determine_emitter(request)
        except ResourceException, exc:
            (status, ret, headers) = (exc.status, exc.content, exc.headers)
            mimetype, emitter = self.emitters[0]
            
        content = emitter(self, request, status, headers).emit(ret)

        # Build the HTTP Response
        resp = HttpResponse(content, mimetype=mimetype, status=status)
        for (key, val) in headers.items():
            resp[key] = val

        return resp

    def _not_implemented(self, operation):
        resource_name = self.__class__.__name__
        raise ResourceException(STATUS_500_INTERNAL_SERVER_ERROR,
                                {'detail': '%s operation on this resource has not been implemented' % (operation, )})

    def read(self, headers={}, *args, **kwargs):
        self._not_implemented('read')

    def create(self, data=None, headers={}, *args, **kwargs):
        self._not_implemented('create')
    
    def update(self, data=None, headers={}, *args, **kwargs):
        self._not_implemented('update')

    def delete(self, headers={}, *args, **kwargs):
        self._not_implemented('delete')

    def reverse(self, view, *args, **kwargs):
        """Return a fully qualified URI for a view, using the current request as the base URI.
        """
        return self._request.build_absolute_uri(reverse(view, *args, **kwargs))
