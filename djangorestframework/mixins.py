"""
The :mod:`mixins` module provides a set of reusable `mixin`
classes that can be added to a `View`.
"""

from django.contrib.auth.models import AnonymousUser
from django.core.paginator import Paginator
from django.db.models.fields.related import ForeignKey
from urlobject import URLObject

from djangorestframework import status
from djangorestframework.renderers import BaseRenderer
from djangorestframework.resources import Resource, FormResource, ModelResource
from djangorestframework.response import Response, ImmediateResponse
from djangorestframework.request import Request
from djangorestframework.utils import as_tuple, allowed_methods


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
    `Mixin` class enabling the use of :class:`request.Request` in your views.
    """

    parser_classes = ()
    """
    The set of parsers that the view can handle.
    Should be a tuple/list of classes as described in the :mod:`parsers` module.
    """

    request_class = Request
    """
    The class to use as a wrapper for the original request object.
    """

    def get_parsers(self):
        """
        Instantiates and returns the list of parsers the request will use.
        """
        return [p(self) for p in self.parser_classes]

    def create_request(self, request):
        """
        Creates and returns an instance of :class:`request.Request`.
        This new instance wraps the `request` passed as a parameter, and use the 
        parsers set on the view.
        """
        parsers = self.get_parsers()
        return self.request_class(request, parsers=parsers)

    @property
    def _parsed_media_types(self):
        """
        Returns a list of all the media types that this view can parse.
        """
        return [p.media_type for p in self.parser_classes]
        

########## ResponseMixin ##########

class ResponseMixin(object):
    """
    `Mixin` class enabling the use of :class:`response.Response` in your views.
    """

    renderer_classes = ()
    """
    The set of response renderers that the view can handle.
    Should be a tuple/list of classes as described in the :mod:`renderers` module.
    """

    def get_renderers(self):
        """
        Instantiates and returns the list of renderers the response will use.
        """
        return [r(self) for r in self.renderer_classes]

    def prepare_response(self, response):
        """
        Prepares and returns `response`.
        This has no effect if the response is not an instance of :class:`response.Response`.
        """
        if hasattr(response, 'request') and response.request is None:
            response.request = self.request

        # set all the cached headers
        for name, value in self.headers.items():
            response[name] = value

        # set the views renderers on the response
        response.renderers = self.get_renderers()
        return response

    @property
    def headers(self):
        """
        Dictionary of headers to set on the response.
        This is useful when the response doesn't exist yet, but you
        want to memorize some headers to set on it when it will exist.
        """
        if not hasattr(self, '_headers'):
            self._headers = {}
        return self._headers

    @property
    def _rendered_media_types(self):
        """
        Return an list of all the media types that this view can render.
        """
        return [renderer.media_type for renderer in self.get_renderers()]

    @property
    def _rendered_formats(self):
        """
        Return a list of all the formats that this view can render.
        """
        return [renderer.format for renderer in self.get_renderers()]


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
        Check user permissions and either raise an ``ImmediateResponse`` or return.
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

        May raise an :class:`response.ImmediateResponse` with status code 400 (Bad Request).
        """
        if not hasattr(self, '_content'):
            self._content = self.validate_request(self.request.DATA, self.request.FILES)
        return self._content

    @property
    def PARAMS(self):
        """
        Returns the cleaned, validated query parameters.

        May raise an :class:`response.ImmediateResponse` with status code 400 (Bad Request).
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
        elif getattr(self, '%s_form' % self.request.method.lower(), None):
            return FormResource(self)
        return Resource(self)

    def validate_request(self, data, files=None):
        """
        Given the request *data* and optional *files*, return the cleaned, validated content.
        May raise an :class:`response.ImmediateResponse` with status code 400 (Bad Request) on failure.
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

    def get_query_kwargs(self, *args, **kwargs):
        """
        Return a dict of kwargs that will be used to build the
        model instance retrieval or to filter querysets.
        """

        kwargs = dict(kwargs)

        # If the URLconf includes a .(?P<format>\w+) pattern to match against
        # a .json, .xml suffix, then drop the 'format' kwarg before
        # constructing the query.
        if BaseRenderer._FORMAT_QUERY_PARAM in kwargs:
            del kwargs[BaseRenderer._FORMAT_QUERY_PARAM]

        return kwargs

    def get_instance_data(self, model, content, **kwargs):
        """
        Returns the dict with the data for model instance creation/update.

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

    def get_instance(self, **kwargs):
        """
        Get a model instance for read/update/delete requests.
        """
        return self.get_queryset().get(**kwargs)

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
        query_kwargs = self.get_query_kwargs(request, *args, **kwargs)

        try:
            self.model_instance = self.get_instance(**query_kwargs)
        except model.DoesNotExist:
            raise ImmediateResponse(status=status.HTTP_404_NOT_FOUND)

        return Response(self.model_instance)


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

        response = Response(instance, status=status.HTTP_201_CREATED)

        # Set headers
        if hasattr(instance, 'get_absolute_url'):
            response['Location'] = self.resource(self).url(instance)
        return response


class UpdateModelMixin(ModelMixin):
    """
    Behavior to update a `model` instance on PUT requests
    """
    def put(self, request, *args, **kwargs):
        model = self.resource.model
        query_kwargs = self.get_query_kwargs(request, *args, **kwargs)

        # TODO: update on the url of a non-existing resource url doesn't work
        # correctly at the moment - will end up with a new url
        try:
            self.model_instance = self.get_instance(**query_kwargs)

            for (key, val) in self.CONTENT.items():
                setattr(self.model_instance, key, val)
        except model.DoesNotExist:
            self.model_instance = model(**self.get_instance_data(model, self.CONTENT, *args, **kwargs))
        self.model_instance.save()
        return Response(self.model_instance)


class DeleteModelMixin(ModelMixin):
    """
    Behavior to delete a `model` instance on DELETE requests
    """
    def delete(self, request, *args, **kwargs):
        model = self.resource.model
        query_kwargs = self.get_query_kwargs(request, *args, **kwargs)

        try:
            instance = self.get_instance(**query_kwargs)
        except model.DoesNotExist:
            raise ImmediateResponse(status=status.HTTP_404_NOT_FOUND)

        instance.delete()
        return Response()


class ListModelMixin(ModelMixin):
    """
    Behavior to list a set of `model` instances on GET requests
    """

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        ordering = self.get_ordering()
        query_kwargs = self.get_query_kwargs(request, *args, **kwargs)

        queryset = queryset.filter(**query_kwargs)
        if ordering:
            queryset = queryset.order_by(*ordering)

        return Response(queryset)


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
        url = url.set_query_param('page', page_number)

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
        if self.request.method.upper() != 'GET':
            return self._resource.filter_response(obj)

        paginator = Paginator(obj, self.get_limit())

        try:
            page_num = int(self.request.GET.get('page', '1'))
        except ValueError:
            raise ImmediateResponse(
                {'detail': 'That page contains no results'},
                status=status.HTTP_404_NOT_FOUND)

        if page_num not in paginator.page_range:
            raise ImmediateResponse(
                {'detail': 'That page contains no results'},
                status=status.HTTP_404_NOT_FOUND)

        page = paginator.page(page_num)

        serialized_object_list = self._resource.filter_response(page.object_list)
        serialized_page_info = self.serialize_page_info(page)

        serialized_page_info['results'] = serialized_object_list

        return serialized_page_info
