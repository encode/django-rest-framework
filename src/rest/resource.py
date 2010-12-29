from django.http import HttpResponse
from decimal import Decimal
from rest import emitters, parsers

class Resource(object):

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
        return self._handle_request(request, *args, **kwargs)

    def __init__(self):
        pass

    def _determine_parser(self, request):
        """Return the appropriate parser for the input, given the client's 'Content-Type' header,
        and the content types that this Resource knows how to parse."""
        print request.META
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

        # TODO: Raise 406, Not Acceptable

    def _handle_request(self, request, *args, **kwargs):
        meth = request.method
        
        # Parse the HTTP Request content
        if meth in ('PUT', 'POST'):
            parser = self._determine_parser(request)
            data = parser(self, request).parse(request.raw_post_data)

        if meth == "POST":
            (status, ret, headers) = self.handle_post(data, request.META, *args, **kwargs)
        else:
            (status, ret, headers) = self.handle_get(request.META, *args, **kwargs)

        # Serialize the HTTP Response content
        mimetype, emitter = self._determine_emitter(request)
        content = emitter(self, status, headers).emit(ret)
        print mimetype, emitter, content

        # Build the HTTP Response
        resp = HttpResponse(content, mimetype=mimetype, status=status)
        for (key, val) in headers.items():
            resp[key] = val

        return resp

    def handle_get(self):
        raise NotImplementedError(self.handle_get)

    def handle_post(self):
        raise NotImplementedError(self.handle_post)