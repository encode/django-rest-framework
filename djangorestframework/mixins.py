"""
The :mod:`mixins` module provides a set of reusable `mixin` 
classes that can be added to a `View`.
"""

from django.contrib.auth.models import AnonymousUser
from django.db.models.query import QuerySet
from django.db.models.fields.related import RelatedField
from django.http import HttpResponse
from django.http.multipartparser import LimitBytes

from djangorestframework import status
from djangorestframework.parsers import FormParser, MultiPartParser
from djangorestframework.resources import Resource, FormResource, ModelResource
from djangorestframework.response import Response, ErrorResponse
from djangorestframework.utils import as_tuple, MSIE_USER_AGENT_REGEX
from djangorestframework.utils.mediatypes import is_form_media_type, order_by_precedence

from decimal import Decimal
import re
from StringIO import StringIO


__all__ = (
    # Base behavior mixins
    'RequestMixin',
    'ResponseMixin',
    'AuthMixin',
    'ResourceMixin',
    # Reverse URL lookup behavior
    'InstanceMixin',
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
    `Mixin` class to provide request parsing behavior.
    """

    _USE_FORM_OVERLOADING = True
    _METHOD_PARAM = '_method'
    _CONTENTTYPE_PARAM = '_content_type'
    _CONTENT_PARAM = '_content'

    """
    The set of request parsers that the view can handle.
    
    Should be a tuple/list of classes as described in the :mod:`parsers` module.
    """
    parsers = ()

    @property
    def method(self):
        """
        Returns the HTTP method.

        This should be used instead of just reading :const:`request.method`, as it allows the `method`
        to be overridden by using a hidden `form` field on a form POST request.
        """
        if not hasattr(self, '_method'):
            self._load_method_and_content_type()
        return self._method


    @property
    def content_type(self):
        """
        Returns the content type header.

        This should be used instead of ``request.META.get('HTTP_CONTENT_TYPE')``,
        as it allows the content type to be overridden by using a hidden form
        field on a form POST request.
        """
        if not hasattr(self, '_content_type'):
            self._load_method_and_content_type()
        return self._content_type


    @property
    def DATA(self):
        """
        Parses the request body and returns the data.

        Similar to ``request.POST``, except that it handles arbitrary parsers,
        and also works on methods other than POST (eg PUT).
        """
        if not hasattr(self, '_data'):
            self._load_data_and_files()
        return self._data


    @property
    def FILES(self):
        """
        Parses the request body and returns the files.
        Similar to ``request.FILES``, except that it handles arbitrary parsers,
        and also works on methods other than POST (eg PUT).
        """
        if not hasattr(self, '_files'):
            self._load_data_and_files()
        return self._files


    def _load_data_and_files(self):
        """
        Parse the request content into self.DATA and self.FILES.
        """
        if not hasattr(self, '_content_type'):
            self._load_method_and_content_type()

        if not hasattr(self, '_data'):
            (self._data, self._files) = self._parse(self._get_stream(), self._content_type)


    def _load_method_and_content_type(self):
        """
        Set the method and content_type, and then check if they've been overridden.
        """
        self._method = self.request.method
        self._content_type = self.request.META.get('HTTP_CONTENT_TYPE', self.request.META.get('CONTENT_TYPE', ''))
        self._perform_form_overloading()


    def _get_stream(self):
        """
        Returns an object that may be used to stream the request content.
        """
        request = self.request

        try:
            content_length = int(request.META.get('CONTENT_LENGTH', request.META.get('HTTP_CONTENT_LENGTH')))
        except (ValueError, TypeError):
            content_length = 0

        # TODO: Add 1.3's LimitedStream to compat and use that.
        # NOTE: Currently only supports parsing request body as a stream with 1.3
        if content_length == 0:
            return None
        elif hasattr(request, 'read'):
             return request
        return StringIO(request.raw_post_data)


    def _perform_form_overloading(self):
        """
        If this is a form POST request, then we need to check if the method and content/content_type have been
        overridden by setting them in hidden form fields or not.
        """

        # We only need to use form overloading on form POST requests.
        if not self._USE_FORM_OVERLOADING or self._method != 'POST' or not is_form_media_type(self._content_type):
            return
        
        # At this point we're committed to parsing the request as form data.
        self._data = data = self.request.POST
        self._files = self.request.FILES

        # Method overloading - change the method and remove the param from the content.
        if self._METHOD_PARAM in data:
            self._method = data[self._METHOD_PARAM].upper()

        # Content overloading - modify the content type, and re-parse.
        if self._CONTENT_PARAM in data and self._CONTENTTYPE_PARAM in data:
            self._content_type = data[self._CONTENTTYPE_PARAM]
            stream = StringIO(data[self._CONTENT_PARAM])
            (self._data, self._files) = self._parse(stream, self._content_type)


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
        Return the view's default parser class.
        """        
        return self.parsers[0]



########## ResponseMixin ##########

class ResponseMixin(object):
    """
    Adds behavior for pluggable `Renderers` to a :class:`views.View` class.
    
    Default behavior is to use standard HTTP Accept header content negotiation.
    Also supports overriding the content type by specifying an ``_accept=`` parameter in the URL.
    Ignores Accept headers from Internet Explorer user agents and uses a sensible browser Accept header instead.
    """

    _ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params
    _IGNORE_IE_ACCEPT_HEADER = True

    """
    The set of response renderers that the view can handle.
    
    Should be a tuple/list of classes as described in the :mod:`renderers` module.    
    """
    renderers = ()


    # TODO: wrap this behavior around dispatch(), ensuring it works
    # out of the box with existing Django classes that use render_to_response.
    def render(self, response):
        """
        Takes a :obj:`Response` object and returns an :obj:`HttpResponse`.
        """
        self.response = response

        try:
            renderer, media_type = self._determine_renderer(self.request)
        except ErrorResponse, exc:
            renderer = self._default_renderer(self)
            media_type = renderer.media_type
            response = exc.response

        # Set the media type of the response
        # Note that the renderer *could* override it in .render() if required.
        response.media_type = renderer.media_type
        
        # Serialize the response content
        if response.has_content_body:
            content = renderer.render(response.cleaned_content, media_type)
        else:
            content = renderer.render()

        # Build the HTTP Response
        resp = HttpResponse(content, mimetype=response.media_type, status=response.status)
        for (key, val) in response.headers.items():
            resp[key] = val

        return resp


    def _determine_renderer(self, request):
        """
        Determines the appropriate renderer for the output, given the client's 'Accept' header,
        and the :attr:`renderers` set on this class.

        Returns a 2-tuple of `(renderer, media_type)`

        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
        """

        if self._ACCEPT_QUERY_PARAM and request.GET.get(self._ACCEPT_QUERY_PARAM, None):
            # Use _accept parameter override
            accept_list = [request.GET.get(self._ACCEPT_QUERY_PARAM)]
        elif (self._IGNORE_IE_ACCEPT_HEADER and
              request.META.has_key('HTTP_USER_AGENT') and
              MSIE_USER_AGENT_REGEX.match(request.META['HTTP_USER_AGENT'])):
            # Ignore MSIE's broken accept behavior and do something sensible instead
            accept_list = ['text/html', '*/*']
        elif request.META.has_key('HTTP_ACCEPT'):
            # Use standard HTTP Accept negotiation
            accept_list = [token.strip() for token in request.META["HTTP_ACCEPT"].split(',')]
        else:
            # No accept header specified
            return (self._default_renderer(self), self._default_renderer.media_type)

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) * len(self.renderers)
        renderers = [renderer_cls(self) for renderer_cls in self.renderers]

        for media_type_lst in order_by_precedence(accept_list):
            for renderer in renderers:
                for media_type in media_type_lst:
                    if renderer.can_handle_response(media_type):
                        return renderer, media_type
       
        # No acceptable renderers were found
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
        Return the view's default renderer class.
        """
        return self.renderers[0]


########## Auth Mixin ##########

class AuthMixin(object):
    """
    Simple :class:`mixin` class to add authentication and permission checking to a :class:`View` class.
    """
    
    """
    The set of authentication types that this view can handle.
   
    Should be a tuple/list of classes as described in the :mod:`authentication` module.    
    """
    authentication = ()

    """
    The set of permissions that will be enforced on this view.
    
    Should be a tuple/list of classes as described in the :mod:`permissions` module.    
    """
    permissions = ()


    @property
    def user(self):
        """
        Returns the :obj:`user` for the current request, as determined by the set of
        :class:`authentication` classes applied to the :class:`View`.  
        """
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
    """
    Provides request validation and response filtering behavior.

    Should be a class as described in the :mod:`resources` module.

    The :obj:`resource` is an object that maps a view onto it's representation on the server.

    It provides validation on the content of incoming requests,
    and filters the object representation into a serializable object for the response.
    """
    resource = None

    @property
    def CONTENT(self):
        """
        Returns the cleaned, validated request content.

        May raise an :class:`response.ErrorResponse` with status code 400 (Bad Request).
        """
        if not hasattr(self, '_content'):
            self._content = self.validate_request(self.DATA, self.FILES)
        return self._content

    @property
    def PARAMS(self):
        """
        Returns the cleaned, validated query parameters.

        May raise an :class:`response.ErrorResponse` with status code 400 (Bad Request).
        """
        return self.validate_request(self.request.GET)

    @property
    def _resource(self):
        if self.resource:
            return self.resource(self)
        elif getattr(self, 'model', None):
            return ModelResource(self)
        elif getattr(self, 'form', None):
            return FormResource(self)
        elif getattr(self, '%s_form' % self.method.lower(), None):
            return FormResource(self)
        return Resource(self)

    def validate_request(self, data, files=None):
        """
        Given the request *data* and optional *files*, return the cleaned, validated content.
        May raise an :class:`response.ErrorResponse` with status code 400 (Bad Request) on failure.
        """
        return self._resource.validate_request(data, files)

    def filter_response(self, obj):
        """
        Given the response content, filter it into a serializable object.
        """
        return self._resource.filter_response(obj)

    def get_bound_form(self, content=None, method=None):
        return self._resource.get_bound_form(content, method=method)



##########

class InstanceMixin(object):
    """
    `Mixin` class that is used to identify a `View` class as being the canonical identifier
    for the resources it is mapped to.
    """

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Store the callable object on the resource class that has been associated with this view.
        """
        view = super(InstanceMixin, cls).as_view(**initkwargs)
        resource = getattr(cls(**initkwargs), 'resource', None)
        if resource:
            # We do a little dance when we store the view callable...
            # we need to store it wrapped in a 1-tuple, so that inspect will treat it
            # as a function when we later look it up (rather than turning it into a method).
            # This makes sure our URL reversing works ok.
            resource.view_callable = (view,)
        return view


########## Model Mixins ##########

class ReadModelMixin(object):
    """
    Behavior to read a `model` instance on GET requests
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
    Behavior to create a `model` instance on POST requests
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
            headers['Location'] = self.resource(self).url(instance)
        return Response(status.HTTP_201_CREATED, instance, headers)


class UpdateModelMixin(object):
    """
    Behavior to update a `model` instance on PUT requests
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
    Behavior to delete a `model` instance on DELETE requests
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
    Behavior to list a set of `model` instances on GET requests
    """

    # NB. Not obvious to me if it would be better to set this on the resource?
    #
    # Presumably it's more useful to have on the view, because that way you can
    # have multiple views across different querysets mapping to the same resource.
    #
    # Perhaps it ought to be:
    #
    # 1) View.queryset
    # 2) if None fall back to Resource.queryset
    # 3) if None fall back to Resource.model.objects.all()
    #
    # Any feedback welcomed.
    queryset = None

    def get(self, request, *args, **kwargs):
        model = self.resource.model

        queryset = self.queryset if self.queryset else model.objects.all()

        if hasattr(self, 'resource'):
            ordering = getattr(self.resource, 'ordering', None)
        else:
            ordering = None

        if ordering:
            args = as_tuple(ordering)
            queryset = queryset.order_by(*args)
        return queryset.filter(**kwargs)


