from djangorestframework.mediatypes import MediaType
from djangorestframework.utils import as_tuple, MSIE_USER_AGENT_REGEX
from djangorestframework.response import ErrorResponse
from djangorestframework.parsers import FormParser, MultipartParser
from djangorestframework import status

from django.http import HttpResponse
from django.http.multipartparser import LimitBytes  # TODO: Use LimitedStream in compat
from StringIO import StringIO
from decimal import Decimal
import re



########## Request Mixin ##########

class RequestMixin(object):
    """Mixin class to provide request parsing behaviour."""

    USE_FORM_OVERLOADING = True
    METHOD_PARAM = "_method"
    CONTENTTYPE_PARAM = "_content_type"
    CONTENT_PARAM = "_content"

    parsers = ()
    validators = ()

    def _get_method(self):
        """
        Returns the HTTP method for the current view.
        """
        if not hasattr(self, '_method'):
            self._method = self.request.method
        return self._method


    def _set_method(self, method):
        """
        Set the method for the current view.
        """
        self._method = method


    def _get_content_type(self):
        """
        Returns a MediaType object, representing the request's content type header.
        """
        if not hasattr(self, '_content_type'):
            content_type = self.request.META.get('HTTP_CONTENT_TYPE', self.request.META.get('CONTENT_TYPE', ''))
            if content_type:
                self._content_type = MediaType(content_type)
            else:
                self._content_type = None
        return self._content_type


    def _set_content_type(self, content_type):
        """
        Set the content type.  Should be a MediaType object.
        """
        self._content_type = content_type


    def _get_accept(self):
        """
        Returns a list of MediaType objects, representing the request's accept header.
        """
        if not hasattr(self, '_accept'):
            accept = self.request.META.get('HTTP_ACCEPT', '*/*')
            self._accept = [MediaType(elem) for elem in accept.split(',')]
        return self._accept


    def _set_accept(self):
        """
        Set the acceptable media types.  Should be a list of MediaType objects.
        """
        self._accept = accept


    def _get_stream(self):
        """
        Returns an object that may be used to stream the request content.
        """
        if not hasattr(self, '_stream'):
            request = self.request

            try:
                content_length = int(request.META.get('CONTENT_LENGTH', request.META.get('HTTP_CONTENT_LENGTH')))
            except (ValueError, TypeError):
                content_length = 0
                
            # Currently only supports parsing request body as a stream with 1.3
            if content_length == 0:
                return None
            elif hasattr(request, 'read'):
                # It's not at all clear if this needs to be byte limited or not.
                # Maybe I'm just being dumb but it looks to me like there's some issues
                # with that in Django.
                #
                # Either:
                #   1. It *can't* be treated as a limited byte stream, and you _do_ need to
                #      respect CONTENT_LENGTH, in which case that ought to be documented,
                #      and there probably ought to be a feature request for it to be
                #      treated as a limited byte stream.
                #   2. It *can* be treated as a limited byte stream, in which case there's a
                #      minor bug in the test client, and potentially some redundant
                #      code in MultipartParser.
                #
                #   It's an issue because it affects if you can pass a request off to code that
                #   does something like:
                #
                #   while stream.read(BUFFER_SIZE):
                #       [do stuff]
                #
                #try:
                #    content_length = int(request.META.get('CONTENT_LENGTH',0))
                #except (ValueError, TypeError):
                #    content_length = 0
                # self._stream = LimitedStream(request, content_length)
                self._stream = request
            else:
                self._stream = StringIO(request.raw_post_data)
        return self._stream


    def _set_stream(self, stream):
        """
        Set the stream representing the request body.
        """
        self._stream = stream


    def _get_raw_content(self):
        """
        Returns the parsed content of the request
        """
        if not hasattr(self, '_raw_content'):
            self._raw_content = self.parse(self.stream, self.content_type)
        return self._raw_content


    def _get_content(self):
        """
        Returns the parsed and validated content of the request
        """
        if not hasattr(self, '_content'):
            self._content = self.validate(self.RAW_CONTENT)

        return self._content


    def perform_form_overloading(self):
        """
        Check the request to see if it is using form POST '_method'/'_content'/'_content_type' overrides.
        If it is then alter self.method, self.content_type, self.CONTENT to reflect that rather than simply
        delegating them to the original request.
        """
        if not self.USE_FORM_OVERLOADING or self.method != 'POST' or not self.content_type.is_form():
            return

        # Temporarily switch to using the form parsers, then parse the content
        parsers = self.parsers
        self.parsers = (FormParser, MultipartParser)
        content = self.RAW_CONTENT
        self.parsers = parsers

        # Method overloading - change the method and remove the param from the content
        if self.METHOD_PARAM in content:
            self.method = content[self.METHOD_PARAM].upper()
            del self._raw_content[self.METHOD_PARAM]

        # Content overloading - rewind the stream and modify the content type
        if self.CONTENT_PARAM in content and self.CONTENTTYPE_PARAM in content:
            self._content_type = MediaType(content[self.CONTENTTYPE_PARAM])
            self._stream = StringIO(content[self.CONTENT_PARAM])
            del(self._raw_content)


    def parse(self, stream, content_type):
        """
        Parse the request content.

        May raise a 415 ErrorResponse (Unsupported Media Type),
        or a 400 ErrorResponse (Bad Request).
        """
        if stream is None or content_type is None:
            return None

        parsers = as_tuple(self.parsers)

        parser = None
        for parser_cls in parsers:
            if parser_cls.handles(content_type):
                parser = parser_cls(self)
                break

        if parser is None:
            raise ErrorResponse(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                    {'error': 'Unsupported media type in request \'%s\'.' %
                                     content_type.media_type})

        return parser.parse(stream)


    def validate(self, content):
        """
        Validate, cleanup, and type-ify the request content.
        """
        for validator_cls in self.validators:
            validator = validator_cls(self)
            content = validator.validate(content)
        return content


    def get_bound_form(self, content=None):
        """
        Return a bound form instance for the given content,
        if there is an appropriate form validator attached to the view.
        """
        for validator_cls in self.validators:
            if hasattr(validator_cls, 'get_bound_form'):
                validator = validator_cls(self)
                return validator.get_bound_form(content)
        return None


    @property
    def parsed_media_types(self):
        """Return an list of all the media types that this view can parse."""
        return [parser.media_type for parser in self.parsers]

    
    @property
    def default_parser(self):
        """Return the view's most preffered renderer.
        (This has no behavioural effect, but is may be used by documenting renderers)"""        
        return self.parsers[0]


    method = property(_get_method, _set_method)
    content_type = property(_get_content_type, _set_content_type)
    accept = property(_get_accept, _set_accept)
    stream = property(_get_stream, _set_stream)
    RAW_CONTENT = property(_get_raw_content)
    CONTENT = property(_get_content)


########## ResponseMixin ##########

class ResponseMixin(object):
    """Adds behaviour for pluggable Renderers to a :class:`.Resource` or Django :class:`View`. class.
    
    Default behaviour is to use standard HTTP Accept header content negotiation.
    Also supports overidding the content type by specifying an _accept= parameter in the URL.
    Ignores Accept headers from Internet Explorer user agents and uses a sensible browser Accept header instead."""

    ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params
    REWRITE_IE_ACCEPT_HEADER = True

    #request = None
    #response = None
    renderers = ()

    #def render_to_response(self, obj):
    #    if isinstance(obj, Response):
    #        response = obj
    #    elif response_obj is not None:
    #        response = Response(status.HTTP_200_OK, obj)
    #    else:
    #        response = Response(status.HTTP_204_NO_CONTENT)

    #    response.cleaned_content = self._filter(response.raw_content)
        
    #    self._render(response)


    #def filter(self, content):
    #    """
    #    Filter the response content.
    #    """
    #    for filterer_cls in self.filterers:
    #        filterer = filterer_cls(self)
    #        content = filterer.filter(content)
    #    return content

        
    def render(self, response):
        """Takes a :class:`Response` object and returns a Django :class:`HttpResponse`."""
        self.response = response

        try:
            renderer = self._determine_renderer(self.request)
        except ErrorResponse, exc:
            renderer = self.default_renderer
            response = exc.response
        
        # Serialize the response content
        if response.has_content_body:
            content = renderer(self).render(output=response.cleaned_content)
        else:
            content = renderer(self).render()
        
        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include the normal deletion response code in the output)
        if response.status == 204:
            response.status = 200

        # Build the HTTP Response
        # TODO: Check if renderer.mimetype is underspecified, or if a content-type header has been set
        resp = HttpResponse(content, mimetype=renderer.media_type, status=response.status)
        for (key, val) in response.headers.items():
            resp[key] = val

        return resp


    def _determine_renderer(self, request):
        """Return the appropriate renderer for the output, given the client's 'Accept' header,
        and the content types that this Resource knows how to serve.
        
        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html"""

        if self.ACCEPT_QUERY_PARAM and request.GET.get(self.ACCEPT_QUERY_PARAM, None):
            # Use _accept parameter override
            accept_list = [request.GET.get(self.ACCEPT_QUERY_PARAM)]
        elif (self.REWRITE_IE_ACCEPT_HEADER and
              request.META.has_key('HTTP_USER_AGENT') and
              MSIE_USER_AGENT_REGEX.match(request.META['HTTP_USER_AGENT'])):
            accept_list = ['text/html', '*/*']
        elif request.META.has_key('HTTP_ACCEPT'):
            # Use standard HTTP Accept negotiation
            accept_list = request.META["HTTP_ACCEPT"].split(',')
        else:
            # No accept header specified
            return self.default_renderer
        
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
            for renderer in self.renderers:
                if renderer.media_type in accept_set:
                    return renderer

            # Return any subtype match
            for renderer in self.renderers:
                if renderer.media_type.split('/')[0] + '/*' in accept_set:
                    return renderer

            # Return default
            if '*/*' in accept_set:
                return self.default_renderer
      

        raise ErrorResponse(status.HTTP_406_NOT_ACCEPTABLE,
                                {'detail': 'Could not satisfy the client\'s Accept header',
                                 'available_types': self.renderted_media_types})

    @property
    def renderted_media_types(self):
        """Return an list of all the media types that this resource can render."""
        return [renderer.media_type for renderer in self.renderers]

    @property
    def default_renderer(self):
        """Return the resource's most prefered renderer.
        (This renderer is used if the client does not send and Accept: header, or sends Accept: */*)"""
        return self.renderers[0]


########## Auth Mixin ##########

class AuthMixin(object):
    """Mixin class to provide authentication and permission checking."""
    authenticators = ()
    permissions = ()

    @property
    def auth(self):
        if not hasattr(self, '_auth'):
            self._auth = self._authenticate()
        return self._auth

    def _authenticate(self):
        for authenticator_cls in self.authenticators:
            authenticator = authenticator_cls(self)
            auth = authenticator.authenticate(self.request)
            if auth:
                return auth
        return None

    # TODO?
    #@property
    #def user(self):
    #    if not has_attr(self, '_user'):
    #        auth = self.auth
    #        if isinstance(auth, User...):
    #            self._user = auth
    #        else:
    #            self._user = getattr(auth, 'user', None)
    #    return self._user

    def check_permissions(self):
        if not self.permissions:
            return

        for permission_cls in self.permissions:
            permission = permission_cls(self)
            if not permission.has_permission(self.auth):
                raise ErrorResponse(status.HTTP_403_FORBIDDEN,
                                   {'detail': 'You do not have permission to access this resource. ' +
                                    'You may need to login or otherwise authenticate the request.'})                


