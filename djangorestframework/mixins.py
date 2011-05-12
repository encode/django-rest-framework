"""
The mixins module provides a set of reusable mixin classes that can be added to a ``View``.
"""

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
    # Base behavior mixins
    'RequestMixin',
    'ResponseMixin',
    'AuthMixin',
    'ResourceMixin',
    # Model behavior mixins
    'ReadModelMixin',
    'CreateModelMixin',
    'UpdateModelMixin',
    'DeleteModelMixin',
    'ListModelMixin'
)


########## Request Mixin ##########

class RequestMixin(object):
    """
    Mixin class to provide request parsing behavior.
    """

    _USE_FORM_OVERLOADING = True
    _METHOD_PARAM = '_method'
    _CONTENTTYPE_PARAM = '_content_type'
    _CONTENT_PARAM = '_content'

    parsers = ()

    @property
    def method(self):
        """
        Returns the HTTP method.
        """
        if not hasattr(self, '_method'):
            self._method = self.request.method
        return self._method


    @property
    def content_type(self):
        """
        Returns the content type header.
        """
        if not hasattr(self, '_content_type'):
            self._content_type = self.request.META.get('HTTP_CONTENT_TYPE', self.request.META.get('CONTENT_TYPE', ''))
        return self._content_type


    @property
    def DATA(self):
        """
        Returns the request data.
        """
        if not hasattr(self, '_data'):
            self._load_data_and_files()
        return self._data


    @property
    def FILES(self):
        """
        Returns the request files.
        """
        if not hasattr(self, '_files'):
            self._load_data_and_files()
        return self._files


    def _load_data_and_files(self):
        """
        Parse the request content into self.DATA and self.FILES.
        """
        stream = self._get_stream()
        (self._data, self._files) = self._parse(stream, self.content_type)


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
                # UPDATE BASED ON COMMENT BELOW:
                #
                # Yup, this was a bug in Django - fixed and waiting check in - see ticket 15785.
                # http://code.djangoproject.com/ticket/15785
                #
                # COMMENT:
                #
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
                self._stream = request
            else:
                self._stream = StringIO(request.raw_post_data)
        return self._stream


    # TODO: Modify this so that it happens implictly, rather than being called explicitly
    # ie accessing any of .DATA, .FILES, .content_type, .method will force
    # form overloading.
    def _perform_form_overloading(self):
        """
        Check the request to see if it is using form POST '_method'/'_content'/'_content_type' overrides.
        If it is then alter self.method, self.content_type, self.CONTENT to reflect that rather than simply
        delegating them to the original request.
        """

        # We only need to use form overloading on form POST requests
        content_type = self.request.META.get('HTTP_CONTENT_TYPE', self.request.META.get('CONTENT_TYPE', ''))
        if not self._USE_FORM_OVERLOADING or self.request.method != 'POST' or not not is_form_media_type(content_type):
            return

        # Temporarily switch to using the form parsers, then parse the content
        parsers = self.parsers
        self.parsers = (FormParser, MultiPartParser)
        content = self.DATA
        self.parsers = parsers

        # Method overloading - change the method and remove the param from the content
        if self._METHOD_PARAM in content:
            self._method = content[self._METHOD_PARAM].upper()
            del self._data[self._METHOD_PARAM]

        # Content overloading - rewind the stream and modify the content type
        if self._CONTENT_PARAM in content and self._CONTENTTYPE_PARAM in content:
            self._content_type = content[self._CONTENTTYPE_PARAM]
            self._stream = StringIO(content[self._CONTENT_PARAM])
            del(self._data)


    def _parse(self, stream, content_type):
        """
        Parse the request content.

        May raise a 415 ErrorResponse (Unsupported Media Type), or a 400 ErrorResponse (Bad Request).
        """
        if stream is None or content_type is None:
            return (None, None)

        parsers = as_tuple(self.parsers)

        for parser_cls in parsers:
            parser = parser_cls(self)
            if parser.can_handle_request(content_type):
                return parser.parse(stream)

        raise ErrorResponse(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            {'error': 'Unsupported media type in request \'%s\'.' %
                            content_type})


    @property
    def _parsed_media_types(self):
        """
        Return a list of all the media types that this view can parse.
        """
        return [parser.media_type for parser in self.parsers]

    
    @property
    def _default_parser(self):
        """
        Return the view's default parser.
        """        
        return self.parsers[0]



########## ResponseMixin ##########

class ResponseMixin(object):
    """
    Adds behavior for pluggable Renderers to a :class:`.BaseView` or Django :class:`View`. class.
    
    Default behavior is to use standard HTTP Accept header content negotiation.
    Also supports overriding the content type by specifying an _accept= parameter in the URL.
    Ignores Accept headers from Internet Explorer user agents and uses a sensible browser Accept header instead.
    """

    _ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params
    _IGNORE_IE_ACCEPT_HEADER = True

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
            renderer = self._default_renderer
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


    # TODO: This should be simpler now.
    #       Add a handles_response() to the renderer, then iterate through the
    #       acceptable media types, ordered by how specific they are,
    #       calling handles_response on each renderer.
    def _determine_renderer(self, request):
        """
        Return the appropriate renderer for the output, given the client's 'Accept' header,
        and the content types that this mixin knows how to serve.

        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
        """

        if self._ACCEPT_QUERY_PARAM and request.GET.get(self._ACCEPT_QUERY_PARAM, None):
            # Use _accept parameter override
            accept_list = [request.GET.get(self._ACCEPT_QUERY_PARAM)]
        elif (self._IGNORE_IE_ACCEPT_HEADER and
              request.META.has_key('HTTP_USER_AGENT') and
              MSIE_USER_AGENT_REGEX.match(request.META['HTTP_USER_AGENT'])):
            accept_list = ['text/html', '*/*']
        elif request.META.has_key('HTTP_ACCEPT'):
            # Use standard HTTP Accept negotiation
            accept_list = request.META["HTTP_ACCEPT"].split(',')
        else:
            # No accept header specified
            return self._default_renderer
        
        # Parse the accept header into a dict of {qvalue: set of media types}
        # We ignore mietype parameters
        accept_dict = {}    
        for token in accept_list:
            components = token.split(';')
            mimetype = components[0].strip()
            qvalue = Decimal('1.0')
            
            if len(components) > 1:
                # Parse items that have a qvalue eg 'text/html; q=0.9'
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
                return self._default_renderer
      

        raise ErrorResponse(status.HTTP_406_NOT_ACCEPTABLE,
                                {'detail': 'Could not satisfy the client\'s Accept header',
                                 'available_types': self._rendered_media_types})

    @property
    def _rendered_media_types(self):
        """
        Return an list of all the media types that this view can render.
        """
        return [renderer.media_type for renderer in self.renderers]

    @property
    def _default_renderer(self):
        """
        Return the view's default renderer.
        """
        return self.renderers[0]


########## Auth Mixin ##########

class AuthMixin(object):
    """
    Simple mixin class to add authentication and permission checking to a ``View`` class.
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


########## Resource Mixin ##########

class ResourceMixin(object):
    @property
    def CONTENT(self):
        if not hasattr(self, '_content'):
            self._content = self._get_content()
        return self._content

    def _get_content(self):
        resource = self.resource(self)
        return resource.validate(self.DATA, self.FILES)

    def get_bound_form(self, content=None):
        resource = self.resource(self)
        return resource.get_bound_form(content)

    def object_to_data(self, obj):
        resource = self.resource(self)
        return resource.object_to_data(obj)


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


