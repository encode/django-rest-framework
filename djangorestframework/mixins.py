""""""

from django.contrib.auth.models import AnonymousUser
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField
from django.http import HttpResponse
from django.http.multipartparser import LimitBytes

from djangorestframework import status
from djangorestframework.parsers import FormParser, MultiPartParser
from djangorestframework.response import Response, ErrorResponse
from djangorestframework.utils import as_tuple, MSIE_USER_AGENT_REGEX
from djangorestframework.utils.mediatypes import is_form_media_type

from decimal import Decimal
import re
from StringIO import StringIO


__all__ = (
    'RequestMixin',
    'ResponseMixin',
    'AuthMixin',
    'ReadModelMixin',
    'CreateModelMixin',
    'UpdateModelMixin',
    'DeleteModelMixin',
    'ListModelMixin'
)


########## Request Mixin ##########

class RequestMixin(object):
    """
    Mixin class to provide request parsing behaviour.
    """

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
        Returns the content type header.
        """
        if not hasattr(self, '_content_type'):
            self._content_type = self.request.META.get('HTTP_CONTENT_TYPE', self.request.META.get('CONTENT_TYPE', ''))
        return self._content_type


    def _set_content_type(self, content_type):
        """
        Set the content type header.
        """
        self._content_type = content_type


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

            # TODO: Add 1.3's LimitedStream to compat and use that.
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
                #      code in MultiPartParser.
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
                #
                # UPDATE: http://code.djangoproject.com/ticket/15785
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

    # TODO: Modify this so that it happens implictly, rather than being called explicitly
    # ie accessing any of .DATA, .FILES, .content_type, .stream or .method will force
    # form overloading.
    def perform_form_overloading(self):
        """
        Check the request to see if it is using form POST '_method'/'_content'/'_content_type' overrides.
        If it is then alter self.method, self.content_type, self.CONTENT to reflect that rather than simply
        delegating them to the original request.
        """
        if not self.USE_FORM_OVERLOADING or self.method != 'POST' or not is_form_media_type(self.content_type):
            return

        # Temporarily switch to using the form parsers, then parse the content
        parsers = self.parsers
        self.parsers = (FormParser, MultiPartParser)
        content = self.RAW_CONTENT
        self.parsers = parsers

        # Method overloading - change the method and remove the param from the content
        if self.METHOD_PARAM in content:
            self.method = content[self.METHOD_PARAM].upper()
            del self._raw_content[self.METHOD_PARAM]

        # Content overloading - rewind the stream and modify the content type
        if self.CONTENT_PARAM in content and self.CONTENTTYPE_PARAM in content:
            self._content_type = content[self.CONTENTTYPE_PARAM]
            self._stream = StringIO(content[self.CONTENT_PARAM])
            del(self._raw_content)


    def parse(self, stream, content_type):
        """
        Parse the request content.

        May raise a 415 ErrorResponse (Unsupported Media Type), or a 400 ErrorResponse (Bad Request).
        """
        if stream is None or content_type is None:
            return None

        parsers = as_tuple(self.parsers)

        for parser_cls in parsers:
            parser = parser_cls(self)
            if parser.can_handle_request(content_type):
                return parser.parse(stream)

        raise ErrorResponse(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            {'error': 'Unsupported media type in request \'%s\'.' %
                            content_type})


    # TODO: Acutally this needs to go into Resource
    def validate(self, content):
        """
        Validate, cleanup, and type-ify the request content.
        """
        for validator_cls in self.validators:
            validator = validator_cls(self)
            content = validator.validate(content)
        return content


    # TODO: Acutally this needs to go into Resource
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
        """Return the view's most preferred parser.
        (This has no behavioral effect, but is may be used by documenting renderers)"""        
        return self.parsers[0]


    method = property(_get_method, _set_method)
    content_type = property(_get_content_type, _set_content_type)
    stream = property(_get_stream, _set_stream)
    RAW_CONTENT = property(_get_raw_content)
    CONTENT = property(_get_content)


########## ResponseMixin ##########

class ResponseMixin(object):
    """
    Adds behavior for pluggable Renderers to a :class:`.BaseView` or Django :class:`View`. class.
    
    Default behavior is to use standard HTTP Accept header content negotiation.
    Also supports overriding the content type by specifying an _accept= parameter in the URL.
    Ignores Accept headers from Internet Explorer user agents and uses a sensible browser Accept header instead.
    """
    ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params
    REWRITE_IE_ACCEPT_HEADER = True

    renderers = ()
     
    # TODO: wrap this behavior around dispatch(), ensuring it works
    # out of the box with existing Django classes that use render_to_response.
    def render(self, response):
        """
        Takes a ``Response`` object and returns an ``HttpResponse``.
        """
        self.response = response

        try:
            renderer = self._determine_renderer(self.request)
        except ErrorResponse, exc:
            renderer = self.default_renderer
            response = exc.response
        
        # Serialize the response content
        # TODO: renderer.media_type isn't the right thing to do here...
        if response.has_content_body:
            content = renderer(self).render(response.cleaned_content, renderer.media_type)
        else:
            content = renderer(self).render()

        # Build the HTTP Response
        # TODO: renderer.media_type isn't the right thing to do here...
        resp = HttpResponse(content, mimetype=renderer.media_type, status=response.status)
        for (key, val) in response.headers.items():
            resp[key] = val

        return resp


    def _determine_renderer(self, request):
        """
        Return the appropriate renderer for the output, given the client's 'Accept' header,
        and the content types that this mixin knows how to serve.
        
        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
        """

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
        """
        Return an list of all the media types that this resource can render.
        """
        return [renderer.media_type for renderer in self.renderers]

    @property
    def default_renderer(self):
        """
        Return the resource's most preferred renderer.
        (This renderer is used if the client does not send and Accept: header, or sends Accept: */*)
        """
        return self.renderers[0]


########## Auth Mixin ##########

class AuthMixin(object):
    """
    Simple mixin class to provide authentication and permission checking,
    by adding a set of authentication and permission classes on a ``View``.
    """
    authentication = ()
    permissions = ()

    @property
    def user(self):
        if not hasattr(self, '_user'):
            self._user = self._authenticate()
        return self._user
    
    def _authenticate(self):
        """
        Attempt to authenticate the request using each authentication class in turn.
        Returns a ``User`` object, which may be ``AnonymousUser``.
        """
        for authentication_cls in self.authentication:
            authentication = authentication_cls(self)
            user = authentication.authenticate(self.request)
            if user:
                return user
        return AnonymousUser()

    # TODO: wrap this behavior around dispatch()
    def _check_permissions(self):
        """
        Check user permissions and either raise an ``ErrorResponse`` or return.
        """
        user = self.user
        for permission_cls in self.permissions:
            permission = permission_cls(self)
            permission.check_permission(user)                


########## Model Mixins ##########

class ReadModelMixin(object):
    """
    Behavior to read a model instance on GET requests
    """
    def get(self, request, *args, **kwargs):
        model = self.resource.model
        try:
            if args:
                # If we have any none kwargs then assume the last represents the primrary key
                instance = model.objects.get(pk=args[-1], **kwargs)
            else:
                # Otherwise assume the kwargs uniquely identify the model
                instance = model.objects.get(**kwargs)
        except model.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)

        return instance


class CreateModelMixin(object):
    """
    Behavior to create a model instance on POST requests
    """
    def post(self, request, *args, **kwargs):        
        model = self.resource.model
        # translated 'related_field' kwargs into 'related_field_id'
        for related_name in [field.name for field in model._meta.fields if isinstance(field, RelatedField)]:
            if kwargs.has_key(related_name):
                kwargs[related_name + '_id'] = kwargs[related_name]
                del kwargs[related_name]

        all_kw_args = dict(self.CONTENT.items() + kwargs.items())
        if args:
            instance = model(pk=args[-1], **all_kw_args)
        else:
            instance = model(**all_kw_args)
        instance.save()
        headers = {}
        if hasattr(instance, 'get_absolute_url'):
            headers['Location'] = instance.get_absolute_url()
        return Response(status.HTTP_201_CREATED, instance, headers)


class UpdateModelMixin(object):
    """
    Behavior to update a model instance on PUT requests
    """
    def put(self, request, *args, **kwargs):
        model = self.resource.model
        # TODO: update on the url of a non-existing resource url doesn't work correctly at the moment - will end up with a new url 
        try:
            if args:
                # If we have any none kwargs then assume the last represents the primrary key
                instance = model.objects.get(pk=args[-1], **kwargs)
            else:
                # Otherwise assume the kwargs uniquely identify the model
                instance = model.objects.get(**kwargs)

            for (key, val) in self.CONTENT.items():
                setattr(instance, key, val)
        except model.DoesNotExist:
            instance = model(**self.CONTENT)
            instance.save()

        instance.save()
        return instance


class DeleteModelMixin(object):
    """
    Behavior to delete a model instance on DELETE requests
    """
    def delete(self, request, *args, **kwargs):
        model = self.resource.model
        try:
            if args:
                # If we have any none kwargs then assume the last represents the primrary key
                instance = model.objects.get(pk=args[-1], **kwargs)
            else:
                # Otherwise assume the kwargs uniquely identify the model
                instance = model.objects.get(**kwargs)
        except model.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND, None, {})

        instance.delete()
        return


class ListModelMixin(object):
    """
    Behavior to list a set of model instances on GET requests
    """
    queryset = None

    def get(self, request, *args, **kwargs):
        queryset = self.queryset if self.queryset else self.resource.model.objects.all()
        return queryset.filter(**kwargs)


