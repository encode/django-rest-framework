from django.http import HttpResponse
from django.core.urlresolvers import reverse
from rest import emitters, parsers
from decimal import Decimal


class Resource(object):

    class HTTPException(Exception):
        def __init__(self, status, content, headers):
            self.status = status
            self.content = content
            self.headers = headers

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
                'application/x-www-form-urlencoded': parsers.FormParser }


    def __new__(cls, request, *args, **kwargs):
        self = object.__new__(cls)
        self.__init__()
        self._request = request
        return self._handle_request(request, *args, **kwargs)

    def __init__(self):
        pass

    def _determine_parser(self, request):
        """Return the appropriate parser for the input, given the client's 'Content-Type' header,
        and the content types that this Resource knows how to parse."""
        return self.parsers.values()[0]
    
        # TODO: Raise 415 Unsupported media type
    
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

        raise self.HTTPException(406, {'status': 'Not Acceptable',
                                       'accepts': ','.join(item[0] for item in self.emitters)}, {})


    def _handle_request(self, request, *args, **kwargs):
        method = request.method

        try:
            if not method in self.allowed_methods:
                raise self.HTTPException(405, {'status': 'Method Not Allowed'}, {})
    
            # Parse the HTTP Request content
            func = getattr(self, self.callmap.get(method, ''))
    
            if method in ('PUT', 'POST'):
                parser = self._determine_parser(request)
                data = parser(self, request).parse(request.raw_post_data)
                (status, ret, headers) = func(data, request.META, *args, **kwargs)
    
            else:
                (status, ret, headers) = func(request.META, *args, **kwargs)
        except self.HTTPException, exc:
            (status, ret, headers) = (exc.status, exc.content, exc.headers)

        headers['Allow'] = ', '.join(self.allowed_methods)
        
        # Serialize the HTTP Response content
        try:        
            mimetype, emitter = self._determine_emitter(request)
        except self.HTTPException, exc:
            (status, ret, headers) = (exc.status, exc.content, exc.headers)
            mimetype, emitter = self.emitters[0]
            
        content = emitter(self, status, headers).emit(ret)

        # Build the HTTP Response
        resp = HttpResponse(content, mimetype=mimetype, status=status)
        for (key, val) in headers.items():
            resp[key] = val

        return resp

    def _not_implemented(self, operation):
        resource_name = self.__class__.__name__
        return (500, {'status': 'Internal Server Error',
                          'detail': '%s %s operation is permitted but has not been implemented' % (resource_name, operation)}, {})

    def read(self, headers={}, *args, **kwargs):
        return self._not_implemented('read')

    def create(self, data=None, headers={}, *args, **kwargs):
        return self._not_implemented('create')
    
    def update(self, data=None, headers={}, *args, **kwargs):
        return self._not_implemented('update')

    def delete(self, headers={}, *args, **kwargs):
        return self._not_implemented('delete')

    def reverse(self, view, *args, **kwargs):
        """Return a fully qualified URI for a view, using the current request as the base URI.
        """
        return self._request.build_absolute_uri(reverse(view, *args, **kwargs))
