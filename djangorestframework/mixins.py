"""
The :mod:`mixins` module provides a set of reusable `mixin`
classes that can be added to a `View`.
"""

from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.db.models.fields.related import ForeignKey
from django.db.models.query import Q
from django.http import HttpResponse
from urlobject import URLObject

from djangorestframework import status
from djangorestframework.renderers import BaseRenderer
from djangorestframework.resources import Resource, FormResource, ModelResource
from djangorestframework.response import Response, ErrorResponse
from djangorestframework.utils import as_tuple, MSIE_USER_AGENT_REGEX
from djangorestframework.utils.mediatypes import is_form_media_type, order_by_precedence

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

    parsers = ()
    """
    The set of request parsers that the view can handle.

    Should be a tuple/list of classes as described in the :mod:`parsers` module.
    """

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

    renderers = ()
    """
    The set of response renderers that the view can handle.

    Should be a tuple/list of classes as described in the :mod:`renderers` module.
    """

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
              'HTTP_USER_AGENT' in request.META and
              MSIE_USER_AGENT_REGEX.match(request.META['HTTP_USER_AGENT'])):
            # Ignore MSIE's broken accept behavior and do something sensible instead
            accept_list = ['text/html', '*/*']
        elif 'HTTP_ACCEPT' in request.META:
            # Use standard HTTP Accept negotiation
            accept_list = [token.strip() for token in request.META['HTTP_ACCEPT'].split(',')]
        else:
            # No accept header specified
            accept_list = ['*/*']

        # Check the acceptable media types against each renderer,
        # attempting more specific media types first
        # NB. The inner loop here isn't as bad as it first looks :)
        #     Worst case is we're looping over len(accept_list) * len(self.renderers)
        renderers = [renderer_cls(self) for renderer_cls in self.renderers]

        for accepted_media_type_lst in order_by_precedence(accept_list):
            for renderer in renderers:
                for accepted_media_type in accepted_media_type_lst:
                    if renderer.can_handle_response(accepted_media_type):
                        return renderer, accepted_media_type

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
    Simple :class:`mixin` class to add authentication and permission checking to a :class:`View` class.
    """

    authentication = ()
    """
    The set of authentication types that this view can handle.

    Should be a tuple/list of classes as described in the :mod:`authentication` module.
    """

    permissions = ()
    """
    The set of permissions that will be enforced on this view.

    Should be a tuple/list of classes as described in the :mod:`permissions` module.
    """

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
        if hasattr(self._resource, 'get_bound_form'):
            return self._resource.get_bound_form(content, method=method)
        else:
            return None

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

class ModelMixin(object):
    """ Implements mechanisms used by other classes (like *ModelMixin group) to
    define a query that represents Model instances the Mixin is working with.

    If a *ModelMixin is going to retrive an instance (or queryset) using args and kwargs
    passed by as URL arguments, it should provied arguments to objects.get and objects.filter
    methods wrapped in by `build_query`

    If a *ModelMixin is going to create/update an instance get_instance_data
    handles the instance data creation/preaparation.
    """

    queryset = None

    def build_query(self, *args, **kwargs):
        """ Returns django.db.models.Q object to be used for the objects retrival.

        Arguments:
        - args: unnamed URL arguments
        - kwargs: named URL arguments

        If a URL passes any arguments to the view being the QueryMixin subclass
        build_query manages the arguments and provides the Q object that will be
        used for the objects retrival with filter/get queryset methods.

        Technically, neither args nor kwargs have to be provided, however the default
        behaviour is to map all kwargs as the query constructors so that if this
        method is not overriden only kwargs keys being model fields are valid.

        If positional args are provided, the last one argument is understood
        as the primary key.  However this usage should be considered
        deperecated, and will be removed in a future version.
        """

        tmp = dict(kwargs)

        # If the URLconf includes a .(?P<format>\w+) pattern to match against
        # a .json, .xml suffix, then drop the 'format' kwarg before
        # constructing the query.
        if BaseRenderer._FORMAT_QUERY_PARAM in tmp:
            del tmp[BaseRenderer._FORMAT_QUERY_PARAM]

        if args:
            # If we have any no kwargs then assume the last arg represents the
            # primrary key. Otherwise assume the kwargs uniquely identify the
            # model.
            tmp.update({'pk': args[-1]})
        return Q(**tmp)

    def get_instance_data(self, model, content, **kwargs):
        """
        Returns the dict with the data for model instance creation/update query.

        Arguments:
        - model: model class (django.db.models.Model subclass) to work with
        - content: a dictionary with instance data
        - kwargs: a dict of URL provided keyword arguments

        The create/update queries are created basicly with the contet provided
        with POST/PUT HTML methods and kwargs passed in the URL. This methods
        simply merges the URL data and the content preaparing the ready-to-use
        data dictionary.
        """

        tmp = dict(kwargs)

        for field in model._meta.fields:
            if isinstance(field, ForeignKey) and field.name in tmp:
                # translate 'related_field' kwargs into 'related_field_id'
                tmp[field.name + '_id'] = tmp[field.name]
                del tmp[field.name]

        all_kw_args = dict(content.items() + tmp.items())

        return all_kw_args

    def get_object(self, *args, **kwargs):
        """
        Get the instance object for read/update/delete requests.
        """
        model = self.resource.model
        return model.objects.get(self.build_query(*args, **kwargs))

    def get_queryset(self):
        """
        Return the queryset for this view.
        """
        return getattr(self.resource, 'queryset',
                       self.resource.model.objects.all())

    def get_ordering(self):
        """
        Return the ordering for this view.
        """
        return getattr(self.resource, 'ordering', None)


class ReadModelMixin(ModelMixin):
    """
    Behavior to read a `model` instance on GET requests
    """
    def get(self, request, *args, **kwargs):
        model = self.resource.model

        try:
            self.model_instance = self.get_object(*args, **kwargs)
        except model.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND)

        return self.model_instance

    def build_query(self, *args, **kwargs):
        # Build query is overriden to filter the kwargs priori
        # to use them as build_query argument
        filtered_keywords = kwargs.copy()

        return super(ReadModelMixin, self).build_query(*args, **filtered_keywords)


class CreateModelMixin(ModelMixin):
    """
    Behavior to create a `model` instance on POST requests
    """
    def post(self, request, *args, **kwargs):
        model = self.resource.model

        # Copy the dict to keep self.CONTENT intact
        content = dict(self.CONTENT)
        m2m_data = {}

        for field in model._meta.many_to_many:
            if field.name in content:
                m2m_data[field.name] = (
                    field.m2m_reverse_field_name(), content[field.name]
                )
                del content[field.name]

        instance = model(**self.get_instance_data(model, content, *args, **kwargs))
        instance.save()

        for fieldname in m2m_data:
            manager = getattr(instance, fieldname)

            if hasattr(manager, 'add'):
                manager.add(*m2m_data[fieldname][1])
            else:
                data = {}
                data[manager.source_field_name] = instance

                for related_item in m2m_data[fieldname][1]:
                    data[m2m_data[fieldname][0]] = related_item
                    manager.through(**data).save()

        headers = {}
        if hasattr(instance, 'get_absolute_url'):
            headers['Location'] = self.resource(self).url(instance)
        return Response(status.HTTP_201_CREATED, instance, headers)


class UpdateModelMixin(ModelMixin):
    """
    Behavior to update a `model` instance on PUT requests
    """
    def put(self, request, *args, **kwargs):
        model = self.resource.model

        # TODO: update on the url of a non-existing resource url doesn't work
        # correctly at the moment - will end up with a new url
        try:
            self.model_instance = self.get_object(*args, **kwargs)

            for (key, val) in self.CONTENT.items():
                setattr(self.model_instance, key, val)
        except model.DoesNotExist:
            self.model_instance = model(**self.get_instance_data(model, self.CONTENT, *args, **kwargs))
        self.model_instance.save()
        return self.model_instance


class DeleteModelMixin(ModelMixin):
    """
    Behavior to delete a `model` instance on DELETE requests
    """
    def delete(self, request, *args, **kwargs):
        model = self.resource.model

        try:
            instance = self.get_object(*args, **kwargs)
        except model.DoesNotExist:
            raise ErrorResponse(status.HTTP_404_NOT_FOUND, None, {})

        instance.delete()
        return


class ListModelMixin(ModelMixin):
    """
    Behavior to list a set of `model` instances on GET requests
    """

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        ordering = self.get_ordering()

        queryset = queryset.filter(self.build_query(**kwargs))
        if ordering:
            queryset = queryset.order_by(*ordering)

        return queryset


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
        """
        Helper method to determine what the `limit` should be
        """
        try:
            limit = int(self.request.GET.get('limit', self.limit))
            return min(limit, self.limit)
        except ValueError:
            return self.limit

    def url_with_page_number(self, page_number):
        """
        Constructs a url used for getting the next/previous urls
        """
        url = URLObject.parse(self.request.get_full_path())
        url = url.add_query_param('page', page_number)

        limit = self.get_limit()
        if limit != self.limit:
            url = url.add_query_param('limit', limit)

        return url

    def next(self, page):
        """
        Returns a url to the next page of results (if any)
        """
        if not page.has_next():
            return None

        return self.url_with_page_number(page.next_page_number())

    def previous(self, page):
        """ Returns a url to the previous page of results (if any) """
        if not page.has_previous():
            return None

        return self.url_with_page_number(page.previous_page_number())

    def serialize_page_info(self, page):
        """
        This is some useful information that is added to the response
        """
        return {
            'next': self.next(page),
            'page': page.number,
            'pages': page.paginator.num_pages,
            'per_page': self.get_limit(),
            'previous': self.previous(page),
            'total': page.paginator.count,
        }

    def filter_response(self, obj):
        """
        Given the response content, paginate and then serialize.

        The response is modified to include to useful data relating to the number
        of objects, number of pages, next/previous urls etc. etc.

        The serialised objects are put into `results` on this new, modified
        response
        """

        # We don't want to paginate responses for anything other than GET requests
        if self.method.upper() != 'GET':
            return self._resource.filter_response(obj)

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

        serialized_object_list = self._resource.filter_response(page.object_list)
        serialized_page_info = self.serialize_page_info(page)

        serialized_page_info['results'] = serialized_object_list

        return serialized_page_info
