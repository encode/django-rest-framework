from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.core.handlers.wsgi import STATUS_CODE_TEXT
from rest import emitters, parsers
from decimal import Decimal
import re

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

    # Some reserved parameters to allow us to use standard HTML forms with our resource.
    METHOD_PARAM = '_method'
    ACCEPT_PARAM = '_accept'
    CSRF_PARAM = 'csrfmiddlewaretoken'
    RESERVED_PARAMS = set((METHOD_PARAM, ACCEPT_PARAM, CSRF_PARAM))

    USE_SITEMAP_FOR_ABSOLUTE_URLS = False


    def __new__(cls, request, *args, **kwargs):
        """Make the class callable so it can be used as a Django view."""
        self = object.__new__(cls)
        self.__init__()
        return self._handle_request(request, *args, **kwargs)


    def __init__(self):
        pass


    def name(self):
        """Provide a name for the resource.
        By default this is the class name, with 'CamelCaseNames' converted to 'Camel Case Names',
        although this behaviour may be overridden."""
        class_name = self.__class__.__name__
        return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', class_name).strip()


    def description(self):
        """Provide a description for the resource.
        By default this is the class's docstring,
        although this behaviour may be overridden."""
        return "%s" % self.__doc__
   
 
    def resp_status_text(self):
        """Return reason text corrosponding to our HTTP response status code.
        Provided for convienience."""
        return STATUS_CODE_TEXT.get(self.resp_status, '')


    def reverse(self, view, *args, **kwargs):
        """Return a fully qualified URI for a given view or resource, using the current request as the base URI.
        TODO: Add SITEMAP option.
        
        Provided for convienience."""
        return self.request.build_absolute_uri(reverse(view, *args, **kwargs))


    def make_absolute(self, uri):
        """Given a relative URI, return an absolute URI using the current request as the base URI.
        TODO: Add SITEMAP option.

        Provided for convienience."""
        return self.request.build_absolute_uri(uri)


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
        method = request.method
        
        if method == 'POST' and request.POST.has_key(self.METHOD_PARAM):
            method = request.POST[self.METHOD_PARAM].upper()
        
        return method


    def authenticate(self):
        """..."""
        # user = ...
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
  
  
    def cleanup_request(self, data):
        """Perform any resource-specific data deserialization and/or validation
        after the initial HTTP content-type deserialization has taken place.
        
        Returns a tuple containing the cleaned up data, and optionally a form bound to that data.
        
        By default this uses form validation to filter the basic input into the required types."""
        if self.form is None:
            return (data, None)

        form_instance = self.get_bound_form(data)

        if not form_instance.is_valid():
            if not form_instance.errors:
                details = 'No content was supplied'
            else:
                details = dict((key, map(unicode, val)) for (key, val) in form_instance.errors.iteritems())
                if form_instance.non_field_errors():
                    details['_extra'] = self.form.non_field_errors()

            raise ResourceException(STATUS_400_BAD_REQUEST, {'detail': details})

        return (form_instance.cleaned_data, form_instance)


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
                (data, self.form_instance) = self.cleanup_request(data)
                (self.resp_status, ret, self.resp_headers) = func(data, request.META, *args, **kwargs)

            else:
                (self.resp_status, ret, self.resp_headers) = func(request.META, *args, **kwargs)
                self.form_instance = self.get_bound_form(ret, is_response=True)


        except ResourceException, exc:
            (self.resp_status, ret, self.resp_headers) = (exc.status, exc.content, exc.headers)
            if emitter is None:
                mimetype, emitter = self.emitters[0] 
            if self.form_instance is None:
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




from django.forms import ModelForm
from django.db.models.query import QuerySet
from django.db.models import Model
import decimal
import inspect

class ModelResource(Resource):
    model = None
    fields = None
    form_fields = None

    def get_bound_form(self, data=None, is_response=False):
        """Return a form that may be used in validation and/or rendering an html emitter"""
        if self.form:
            return super(self.__class__, self).get_bound_form(data, is_response=is_response)

        elif self.model:
            class NewModelForm(ModelForm):
                class Meta:
                    model = self.model
                    fields = self.form_fields if self.form_fields else None #self.fields
                    
            if data and not is_response:
                return NewModelForm(data)
            elif data and is_response:
                return NewModelForm(instance=data)
            else:
                return NewModelForm()
        
        else:
            return None
    


    def cleanup_response(self, data):
        """
        Recursively serialize a lot of types, and
        in cases where it doesn't recognize the type,
        it will fall back to Django's `smart_unicode`.
        
        Returns `dict`.
        """

        def _any(thing, fields=()):
            """
            Dispatch, all types are routed through here.
            """
            ret = None
            
            if isinstance(thing, QuerySet):
                ret = _qs(thing, fields=fields)
            elif isinstance(thing, (tuple, list)):
                ret = _list(thing)
            elif isinstance(thing, dict):
                ret = _dict(thing)
            elif isinstance(thing, int):
                ret = thing
            elif isinstance(thing, bool):
                ret = thing
            elif isinstance(thing, type(None)):
                ret = thing
            elif isinstance(thing, decimal.Decimal):
                ret = str(thing)
            elif isinstance(thing, Model):
                ret = _model(thing, fields=fields)
            #elif isinstance(thing, HttpResponse):    TRC
            #    raise HttpStatusCode(thing)
            elif inspect.isfunction(thing):
                if not inspect.getargspec(thing)[0]:
                    ret = _any(thing())
            elif hasattr(thing, '__emittable__'):
                f = thing.__emittable__
                if inspect.ismethod(f) and len(inspect.getargspec(f)[0]) == 1:
                    ret = _any(f())
            else:
                ret = str(thing)  # TRC  TODO: Change this back!

            return ret

        def _fk(data, field):
            """
            Foreign keys.
            """
            return _any(getattr(data, field.name))
        
        def _related(data, fields=()):
            """
            Foreign keys.
            """
            return [ _model(m, fields) for m in data.iterator() ]
        
        def _m2m(data, field, fields=()):
            """
            Many to many (re-route to `_model`.)
            """
            return [ _model(m, fields) for m in getattr(data, field.name).iterator() ]
        

        def _method_fields(data, fields):
            if not data:
                return { }
    
            has = dir(data)
            ret = dict()
                
            for field in fields:
                if field in has:
                    ret[field] = getattr(data, field)
            
            return ret

        def _model(data, fields=()):
            """
            Models. Will respect the `fields` and/or
            `exclude` on the handler (see `typemapper`.)
            """
            ret = { }
            #handler = self.in_typemapper(type(data), self.anonymous)  # TRC
            handler = None                                             # TRC
            get_absolute_url = False
            
            if handler or fields:
                v = lambda f: getattr(data, f.attname)

                if not fields:
                    """
                    Fields was not specified, try to find teh correct
                    version in the typemapper we were sent.
                    """
                    mapped = self.in_typemapper(type(data), self.anonymous)
                    get_fields = set(mapped.fields)
                    exclude_fields = set(mapped.exclude).difference(get_fields)
                
                    if not get_fields:
                        get_fields = set([ f.attname.replace("_id", "", 1)
                            for f in data._meta.fields ])
                
                    # sets can be negated.
                    for exclude in exclude_fields:
                        if isinstance(exclude, basestring):
                            get_fields.discard(exclude)
                            
                        elif isinstance(exclude, re._pattern_type):
                            for field in get_fields.copy():
                                if exclude.match(field):
                                    get_fields.discard(field)
                    
                    get_absolute_url = True

                else:
                    get_fields = set(fields)
                    if 'absolute_url' in get_fields:   # MOVED (TRC)
                        get_absolute_url = True

                met_fields = _method_fields(handler, get_fields)  # TRC

                for f in data._meta.local_fields:
                    if f.serialize and not any([ p in met_fields for p in [ f.attname, f.name ]]):
                        if not f.rel:
                            if f.attname in get_fields:
                                ret[f.attname] = _any(v(f))
                                get_fields.remove(f.attname)
                        else:
                            if f.attname[:-3] in get_fields:
                                ret[f.name] = _fk(data, f)
                                get_fields.remove(f.name)
                
                for mf in data._meta.many_to_many:
                    if mf.serialize and mf.attname not in met_fields:
                        if mf.attname in get_fields:
                            ret[mf.name] = _m2m(data, mf)
                            get_fields.remove(mf.name)
                
                # try to get the remainder of fields
                for maybe_field in get_fields:
                    
                    if isinstance(maybe_field, (list, tuple)):
                        model, fields = maybe_field
                        inst = getattr(data, model, None)

                        if inst:
                            if hasattr(inst, 'all'):
                                ret[model] = _related(inst, fields)
                            elif callable(inst):
                                if len(inspect.getargspec(inst)[0]) == 1:
                                    ret[model] = _any(inst(), fields)
                            else:
                                ret[model] = _model(inst, fields)

                    elif maybe_field in met_fields:
                        # Overriding normal field which has a "resource method"
                        # so you can alter the contents of certain fields without
                        # using different names.
                        ret[maybe_field] = _any(met_fields[maybe_field](data))

                    else:                    
                        maybe = getattr(data, maybe_field, None)
                        if maybe:
                            if callable(maybe):
                                if len(inspect.getargspec(maybe)[0]) == 1:
                                    ret[maybe_field] = _any(maybe())
                            else:
                                ret[maybe_field] = _any(maybe)
                        else:
                            pass   # TRC
                            #handler_f = getattr(handler or self.handler, maybe_field, None)
                            #
                            #if handler_f:
                            #    ret[maybe_field] = _any(handler_f(data))

            else:
                # Add absolute_url if it exists
                get_absolute_url = True
                
                # Add all the fields
                for f in data._meta.fields:
                    if f.attname != 'id':
                        ret[f.attname] = _any(getattr(data, f.attname))
                
                # Add all the propertiess
                klass = data.__class__
                for attr in dir(klass):
                    if not attr.startswith('_') and not attr in ('pk','id') and isinstance(getattr(klass, attr, None), property):
                        #if attr.endswith('_url') or attr.endswith('_uri'):
                        #    ret[attr] = self.make_absolute(_any(getattr(data, attr)))
                        #else:
                        ret[attr] = _any(getattr(data, attr))
                #fields = dir(data.__class__) + ret.keys()
                #add_ons = [k for k in dir(data) if k not in fields and not k.startswith('_')]
                #print add_ons
                ###print dir(data.__class__)
                #from django.db.models import Model
                #model_fields = dir(Model)

                #for attr in dir(data):
                ##    #if attr.startswith('_'):
                ##    #    continue
                #    if (attr in fields) and not (attr in model_fields) and not attr.startswith('_'):
                #        print attr, type(getattr(data, attr, None)), attr in fields, attr in model_fields
                
                #for k in add_ons:
                #    ret[k] = _any(getattr(data, k))
            
            # TRC
            # resouce uri
            #if self.in_typemapper(type(data), self.anonymous):
            #    handler = self.in_typemapper(type(data), self.anonymous)
            #    if hasattr(handler, 'resource_uri'):
            #        url_id, fields = handler.resource_uri()
            #        ret['resource_uri'] = permalink( lambda: (url_id, 
            #            (getattr(data, f) for f in fields) ) )()
            
            # TRC
            #if hasattr(data, 'get_api_url') and 'resource_uri' not in ret:
            #    try: ret['resource_uri'] = data.get_api_url()
            #    except: pass
            
            # absolute uri
            if hasattr(data, 'get_absolute_url') and get_absolute_url:
                try: ret['absolute_url'] = self.make_absolute(data.get_absolute_url())
                except: pass
            
            for key, val in ret.items():
                if key.endswith('_url') or key.endswith('_uri'):
                    ret[key] = self.make_absolute(val)

            return ret
        
        def _qs(data, fields=()):
            """
            Querysets.
            """
            return [ _any(v, fields) for v in data ]
                
        def _list(data):
            """
            Lists.
            """
            return [ _any(v) for v in data ]
            
        def _dict(data):
            """
            Dictionaries.
            """
            return dict([ (k, _any(v)) for k, v in data.iteritems() ])
            
        # Kickstart the seralizin'.
        return _any(data, self.fields)


    def create(self, data, headers={}, *args, **kwargs):
        all_kw_args = dict(data.items() + kwargs.items())
        instance = self.model(**all_kw_args)
        instance.save()
        headers = {}
        if hasattr(instance, 'get_absolute_url'):
            headers['Location'] = self.make_absolute(instance.get_absolute_url())
        return (201, instance, headers)

    def read(self, headers={}, *args, **kwargs):
        try:
            instance = self.model.objects.get(**kwargs)
        except self.model.DoesNotExist:
            return (404, None, {})

        return (200, instance, {})

    def update(self, data, headers={}, *args, **kwargs):
        try:
            instance = self.model.objects.get(**kwargs)    
            for (key, val) in data.items():
                setattr(instance, key, val)
        except self.model.DoesNotExist:
            instance = self.model(**data)
            instance.save()

        instance.save()
        return (200, instance, {})

    def delete(self, headers={}, *args, **kwargs):
        instance = self.model.objects.get(**kwargs)
        instance.delete()
        return (204, None, {})
        


class QueryModelResource(ModelResource):
    allowed_methods = ('read',)

    def get_bound_form(self, data=None, is_response=False):
        return None

    def read(self, headers={}, *args, **kwargs):
        query = self.model.objects.all()
        return (200, query, {})
