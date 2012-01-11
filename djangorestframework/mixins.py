"""
The :mod:`mixins` module provides a set of reusable `mixin`
classes that can be added to a `View`.
"""

from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.http import HttpResponse

from djangorestframework import status
from djangorestframework.resources import Resource
from djangorestframework.response import Response, ErrorResponse
from djangorestframework.utils import MSIE_USER_AGENT_REGEX
from djangorestframework.utils.mediatypes import is_form_media_type, order_by_precedence

from StringIO import StringIO


__all__ = (
    # Base behavior mixins
    'RequestMixin',
    'ResponseMixin',
    'AuthMixin',
    'ResourceMixin',
    'SerializerMixin',
    # Reverse URL lookup behavior
    'InstanceMixin',
    # Model behavior mixins
    'GetResourceMixin',
    'PostResourceMixin',
    'PutResourceMixin',
    'DeleteResourceMixin',
    'ListResourceMixin',
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

        This should be used instead of just reading :const:`request.method`, as
        it allows the `method` to be overridden by using a hidden `form` field
        on a form POST request.
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
            (self._data, self._files) = self._parse(self._get_stream(),
                                                    self._content_type)

    def _load_method_and_content_type(self):
        """
        Set the method and content_type, and then check if they've been
        overridden.
        """
        self._method = self.request.method
        self._content_type = self.request.META.get('HTTP_CONTENT_TYPE',
                                self.request.META.get('CONTENT_TYPE', ''))
        self._perform_form_overloading()

    def _get_stream(self):
        """
        Returns an object that may be used to stream the request content.
        """
        request = self.request

        try:
            content_length = int(request.META.get('CONTENT_LENGTH',
                                    request.META.get('HTTP_CONTENT_LENGTH')))
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
        If this is a form POST request, then we need to check if the method and
        content/content_type have been overridden by setting them in hidden
        form fields or not.
        """

        # We only need to use form overloading on form POST requests.
        if (not self._USE_FORM_OVERLOADING
            or self._method != 'POST'
            or not is_form_media_type(self._content_type)):
            return

        # At this point we're committed to parsing the request as form data.
        self._data = data = self.request.POST.copy()
        self._files = self.request.FILES

        # Method overloading - change the method and remove the param from the content.
        if self._METHOD_PARAM in data:
            # NOTE: unlike `get`, `pop` on a `QueryDict` seems to return a list of values.
            self._method = self._data.pop(self._METHOD_PARAM)[0].upper()

        # Content overloading - modify the content type, and re-parse.
        if self._CONTENT_PARAM in data and self._CONTENTTYPE_PARAM in data:
            self._content_type = self._data.pop(self._CONTENTTYPE_PARAM)[0]
            stream = StringIO(self._data.pop(self._CONTENT_PARAM)[0])
            (self._data, self._files) = self._parse(stream, self._content_type)

    def _parse(self, stream, content_type):
        """
        Parse the request content.

        May raise a 415 ErrorResponse (Unsupported Media Type), or a 400
        ErrorResponse (Bad Request).
        """
        if stream is None or content_type is None:
            return (None, None)

        for parser_cls in self.parsers:
            parser = parser_cls(self)
            if parser.can_handle_request(content_type):
                return parser.parse(stream)

        error = {'error':
                 "Unsupported media type in request '%s'." % content_type}
        raise ErrorResponse(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, error)

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

    Also supports overriding the content type by specifying an ``_accept=``
    parameter in the URL.

    Ignores Accept headers from Internet Explorer user agents and uses a
    sensible browser Accept header instead.
    """

    # Allow override of Accept header in URL query params
    _ACCEPT_QUERY_PARAM = '_accept'
    _IGNORE_IE_ACCEPT_HEADER = True

    """
    The set of response renderers that the view can handle.

    Should be a tuple/list of classes as described in the :mod:`renderers`
    module.
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
        resp = HttpResponse(content, mimetype=response.media_type,
                            status=response.status)
        for (key, val) in response.headers.items():
            resp[key] = val

        return resp

    def _determine_renderer(self, request):
        """
        Determines the appropriate renderer for the output, given the client's
        'Accept' header, and the :attr:`renderers` set on this class.

        Returns a 2-tuple of `(renderer, media_type)`

        See: RFC 2616, Section 14
        http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html
        """

        if (self._ACCEPT_QUERY_PARAM and
            request.GET.get(self._ACCEPT_QUERY_PARAM, None)):
            # Use _accept parameter override
            accept_list = [request.GET.get(self._ACCEPT_QUERY_PARAM)]

        elif (self._IGNORE_IE_ACCEPT_HEADER and
              'HTTP_USER_AGENT' in request.META and
              MSIE_USER_AGENT_REGEX.match(request.META['HTTP_USER_AGENT'])):
            # Ignore MSIE's broken accept behavior and do something sensible
            # instead.
            accept_list = ['text/html', '*/*']

        elif 'HTTP_ACCEPT' in request.META:
            # Use standard HTTP Accept negotiation
            accept_list = [token.strip() for token in
                           request.META['HTTP_ACCEPT'].split(',')]

        else:
            # No accept header specified
            accept_list = ['*/*']

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is: len(accept_list) * len(self.renderers)
        renderers = [renderer_cls(self) for renderer_cls in self.renderers]

        for accepted_media_type_lst in order_by_precedence(accept_list):
            for renderer in renderers:
                for accepted_media_type in accepted_media_type_lst:
                    if renderer.can_handle_response(accepted_media_type):
                        return renderer, accepted_media_type

        # No acceptable renderers were found
        error = {'detail': "Could not satisfy the client's Accept header",
                 'available_types': self._rendered_media_types}
        raise ErrorResponse(status.HTTP_406_NOT_ACCEPTABLE, error)

    @property
    def _rendered_media_types(self):
        """
        Return an list of all the media types that this view can render.
        """
        return [renderer.media_type for renderer in self.renderers]

    @property
    def _rendered_formats(self):
        """
        Return a list of all the formats that this view can render.
        """
        return [renderer.format for renderer in self.renderers]

    @property
    def _default_renderer(self):
        """
        Return the view's default renderer class.
        """
        return self.renderers[0]


########## Auth Mixin ##########

class AuthMixin(object):
    """
    Simple :class:`mixin` class to add authentication and permission checking
    to a :class:`View` class.
    """

    """
    The set of authentication types that this view can handle.

    Should be a tuple/list of classes as described in the :mod:`authentication`
    module.
    """
    authentication = ()

    """
    The set of permissions that will be enforced on this view.

    Should be a tuple/list of classes as described in the :mod:`permissions`
    module.
    """
    permissions = ()

    @property
    def user(self):
        """
        Returns the :obj:`user` for the current request, as determined by the
        set of :class:`authentication` classes applied to the :class:`View`.
        """
        if not hasattr(self, '_user'):
            self._user = self._authenticate()
        return self._user

    def _authenticate(self):
        """
        Attempt to authenticate the request using each authentication class in
        turn.  Returns a ``User`` object, which may be ``AnonymousUser``.
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


class SerializerMixin(object):
    serializer_class = None
    deserializer_class = None

    @property
    def serializer(self):
        if not hasattr(self, '_serializer'):
            self._serializer = self.resource_class(view=self)
        return self._serializer

    @property
    def deserializer(self):
        if not hasattr(self, '_deserializer'):
            self._deserializer = self.resource_class(view=self)
        return self._deserializer

    def deserialize(self, data, files=None):
        """
        Given the request *data* and optional *files*, return the cleaned,
        validated content.
        May raise an :class:`response.ErrorResponse` with status code 400
        (Bad Request) on failure.
        """
        return self.deserializer.deserialize(data, files)

    def serialize(self, obj):
        """
        Given the response content, filter it into a serializable object.
        """
        return self.serializer.serialize(obj)

    def get_bound_form(self, content=None, method=None):
        if hasattr(self.deserializer, 'get_bound_form'):
            return self.deserializer.get_bound_form(content, method=method)
        else:
            return None


########## Resource Mixin ##########

class ResourceMixin(object):
    """
    Provides request validation and response filtering behavior.

    Should be a class as described in the :mod:`resources` module.

    The :obj:`resource` is an object that maps a view onto it's representation
    on the server.

    It provides validation on the content of incoming requests,
    and filters the object representation into a serializable object for the
    response.
    """
    resource_class = Resource

    @property
    def CONTENT(self):
        """
        Returns the cleaned, validated request content.

        May raise an :class:`response.ErrorResponse` with status code 400
        (Bad Request).
        """
        if not hasattr(self, '_content'):
            self._content = self.deserialize(self.DATA, self.FILES)
        return self._content

    @property
    def PARAMS(self):
        """
        Returns the cleaned, validated query parameters.

        May raise an :class:`response.ErrorResponse` with status code 400
        (Bad Request).
        """
        return self.deserialize(self.request.GET)

    def get_resource_class(self):
        if self.resource_class:
            return self.resource_class
        elif getattr(self, 'model', None):
            return ModelResource
        elif getattr(self, 'form', None):
            return FormResource
        elif hasattr(self, 'request') and getattr(self, '%s_form' % self.method.lower(), None):
            return FormResource
        else:
            return Resource

    def get_resource(self):
        resource_class = self.get_resource_class()
        return resource_class(view=self)



##########


class InstanceMixin(object):
    """
    `Mixin` class that is used to identify a `View` class as being the
    canonical identifier for the resources it is mapped to.
    """

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Store the callable object on the resource class that has been
        associated with this view.
        """
        view = super(InstanceMixin, cls).as_view(**initkwargs)
        # TODO: FIX !!! Very bad now, since this is attached on the class (thread-safety)
        resource_class = getattr(cls(**initkwargs), 'resource_class', None)
        if resource_class:
            # We do a little dance when we store the view callable...
            # we need to store it wrapped in a 1-tuple, so that inspect will
            # treat it as a function when we later look it up (rather than
            # turning it into a method).
            # This makes sure our URL reversing works ok.
            resource_class.view_callable = (view,)
        return view


########## Resource operation Mixins ##########

class GetResourceMixin(object):

    def get(self, request, *args, **kwargs):
        resource = self.get_resource()
        try:
            resource.retrieve(*args, **kwargs)
        except resource.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)
        return resource.instance


class PostResourceMixin(object):

    def post(self, request, *args, **kwargs):
        resource = self.get_resource()
        resource.create(*args, **kwargs)
        resource.update(self.CONTENT, *args, **kwargs)
        headers = {'Location': resource.get_url()}
        return Response(status.HTTP_201_CREATED, resource.instance, headers)


class PutResourceMixin(object):

    def put(self, request, *args, **kwargs):
        resource = self.get_resource()
        try:
            resource.retrieve(*args, **kwargs)
            status_code = status.HTTP_204_NO_CONTENT
        except resource.DoesNotExist:
            resource.create(*args, **kwargs)
            status_code = status.HTTP_201_CREATED
        resource.update(self.CONTENT, *args, **kwargs)
        return Response(status_code, resource.instance, {})


class DeleteResourceMixin(object):

    def delete(self, request, *args, **kwargs):
        resource = self.get_resource()
        try:
            resource.retrieve(*args, **kwargs)
        except resource.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)
        resource.delete(*args, **kwargs)
        return


class ListResourceMixin(object):

    def get(self, request, *args, **kwargs):
        resource = self.get_resource()
        return resource.list(*args, **kwargs)


########## Pagination Mixins ##########

class PaginatorMixin(object):
    """
    Adds pagination support to GET requests
    Obviously should only be used on lists :)

    A default limit can be set by setting `limit` on the object. This will also
    be used as the maximum if the client sets the `limit` GET param
    """
    limit = 20

    def get_limit(self):
        """ Helper method to determine what the `limit` should be """
        try:
            limit = int(self.request.GET.get('limit', self.limit))
            return min(limit, self.limit)
        except ValueError:
            return self.limit

    def url_with_page_number(self, page_number):
        """Constructs a url used for getting the next/previous urls."""
        url = "%s?page=%d" % (self.request.path, page_number)

        limit = self.get_limit()
        if limit != self.limit:
            url = "%s&limit=%d" % (url, limit)

        return url

    def next(self, page):
        """Returns a url to the next page of results. (If any exists.)"""
        if not page.has_next():
            return None

        return self.url_with_page_number(page.next_page_number())

    def previous(self, page):
        """Returns a url to the previous page of results. (If any exists.)"""
        if not page.has_previous():
            return None

        return self.url_with_page_number(page.previous_page_number())

    def serialize_page_info(self, page):
        """This is some useful information that is added to the response."""
        return {
            'next': self.next(page),
            'page': page.number,
            'pages': page.paginator.num_pages,
            'per_page': self.get_limit(),
            'previous': self.previous(page),
            'total': page.paginator.count,
        }

    def serialize(self, obj):
        """
        Given the response content, paginate and then serialize.

        The response is modified to include to useful data relating to the
        number of objects, number of pages, next/previous urls etc. etc.

        The serialised objects are put into `results` on this new, modified
        response
        """

        # We don't want to paginate responses for anything other than GET
        # requests
        if self.method.upper() != 'GET':
            return self.serializer.serialize(obj)

        paginator = Paginator(obj, self.get_limit())

        try:
            page_num = int(self.request.GET.get('page', '1'))
        except ValueError:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,
                                {'detail': 'That page contains no results'})

        if page_num not in paginator.page_range:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND,
                                {'detail': 'That page contains no results'})

        page = paginator.page(page_num)

        serialized_object_list = self.serializer.serialize(page.object_list)
        serialized_page_info = self.serialize_page_info(page)

        serialized_page_info['results'] = serialized_object_list

        return serialized_page_info
