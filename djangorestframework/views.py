"""
The :mod:`views` module provides the Views you will most probably
be subclassing in your implementation.

By setting or modifying class attributes on your view, you change it's predefined behaviour.
"""

import re
from django.core.urlresolvers import set_script_prefix, get_script_prefix
from django.http import HttpResponse
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt

from djangorestframework.compat import View as DjangoView, apply_markdown
from djangorestframework.response import Response, ErrorResponse
from djangorestframework.mixins import *
from djangorestframework import resources, renderers, parsers, authentication, permissions, status


__all__ = (
    'View',
    'ModelView',
    'InstanceModelView',
    'ListModelView',
    'ListOrCreateModelView'
)


class View(ResourceMixin, RequestMixin, ResponseMixin, AuthMixin, DjangoView):
    """
    Handles incoming requests and maps them to REST operations.
    Performs request deserialization, response serialization, authentication and input validation.
    """

    resource = None
    """
    The resource to use when validating requests and filtering responses,
    or `None` to use default behaviour.
    """

    renderers = renderers.DEFAULT_RENDERERS
    """
    List of renderers the resource can serialize the response with, ordered by preference.
    """

    parsers = parsers.DEFAULT_PARSERS
    """
    List of parsers the resource can parse the request with.
    """

    authentication = (authentication.UserLoggedInAuthentication,
                       authentication.BasicAuthentication)
    """
    List of all authenticating methods to attempt.
    """

    permissions = (permissions.FullAnonAccess,)
    """
    List of all permissions that must be checked.
    """

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Override the default :meth:`as_view` to store an instance of the view
        as an attribute on the callable function.  This allows us to discover
        information about the view when we do URL reverse lookups.
        """
        view = super(View, cls).as_view(**initkwargs)
        view.cls_instance = cls(**initkwargs)
        return view

    @property
    def allowed_methods(self):
        """
        Return the list of allowed HTTP methods, uppercased.
        """
        return [method.upper() for method in self.http_method_names if hasattr(self, method)]

    def get_name(self):
        """
        Return the resource or view class name for use as this view's name.
        Override to customize.
        """
        # If this view has a resource that's been overridden, then use that resource for the name
        if getattr(self, 'resource', None) not in (None, resources.Resource, resources.FormResource, resources.ModelResource):
            name = self.resource.__name__

            # Chomp of any non-descriptive trailing part of the resource class name
            if name.endswith('Resource') and name != 'Resource':
                name = name[:-len('Resource')]

            # If the view has a descriptive suffix, eg '*** List', '*** Instance'
            if getattr(self, '_suffix', None):
                name += self._suffix
        # If it's a view class with no resource then grok the name from the class name
        elif getattr(self, '__class__', None) is not None:
            name = self.__class__.__name__

            # Chomp of any non-descriptive trailing part of the view class name
            if name.endswith('View') and name != 'View':
                name = name[:-len('View')]
        else:
            name = ''
        return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', name).strip()

    def get_description(self, html=False):
        """
        Return the resource or view docstring for use as this view's description.
        Override to customize.
        """
        # If this view has a resource that's been overridden, then use the resource's doctring
        if getattr(self, 'resource', None) not in (None, resources.Resource, resources.FormResource, resources.ModelResource):
            doc = self.resource.__doc__
        # Otherwise use the view doctring
        elif getattr(self, '__doc__', None):
            doc = self.__doc__
        else:
            doc = ''
        whitespace_counts = [len(line) - len(line.lstrip(' ')) for line in doc.splitlines()[1:] if line.lstrip()]
        # unindent the docstring if needed
        if whitespace_counts:
            whitespace_pattern = '^' + (' ' * min(whitespace_counts))
            doc = re.sub(re.compile(whitespace_pattern, re.MULTILINE), '', doc)
        if doc and html:
            if apply_markdown:
                doc = apply_markdown(doc)
            else:
                doc = escape(doc)
                doc = mark_safe(doc.replace('\n', '<br />'))
        return doc

    def http_method_not_allowed(self, request, *args, **kwargs):
        """
        Return an HTTP 405 error if an operation is called which does not have a handler method.
        """
        raise ErrorResponse(status.HTTP_405_METHOD_NOT_ALLOWED,
                            {'detail': 'Method \'%s\' not allowed on this resource.' % self.method})

    def initial(self, request, *args, **kargs):
        """
        Hook for any code that needs to run prior to anything else.
        Required if you want to do things like set `request.upload_handlers` before
        the authentication and dispatch handling is run.
        """
        # Calls to 'reverse' will not be fully qualified unless we set the
        # scheme/host/port here.
        self.orig_prefix = get_script_prefix()
        if not (self.orig_prefix.startswith('http:') or self.orig_prefix.startswith('https:')):
            prefix = '%s://%s' % (request.is_secure() and 'https' or 'http', request.get_host())
            set_script_prefix(prefix + self.orig_prefix)

    def final(self, request, response, *args, **kargs):
        """
        Hook for any code that needs to run after everything else in the view.
        """
        # Restore script_prefix.
        set_script_prefix(self.orig_prefix)

        # Always add these headers.
        response.headers['Allow'] = ', '.join(self.allowed_methods)
        # sample to allow caching using Vary http header
        response.headers['Vary'] = 'Authenticate, Accept'

        # merge with headers possibly set at some point in the view
        response.headers.update(self.headers)
        return self.render(response)

    def add_header(self, field, value):
        """
        Add *field* and *value* to the :attr:`headers` attribute of the :class:`View` class.
        """
        self.headers[field] = value

    # Note: session based authentication is explicitly CSRF validated,
    # all other authentication is CSRF exempt.
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.headers = {}

        try:
            self.initial(request, *args, **kwargs)

            # Authenticate and check request has the relevant permissions
            self._check_permissions()

            # Get the appropriate handler method
            if self.method.lower() in self.http_method_names:
                handler = getattr(self, self.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response_obj = handler(request, *args, **kwargs)

            # Allow return value to be either HttpResponse, Response, or an object, or None
            if isinstance(response_obj, HttpResponse):
                return response_obj
            elif isinstance(response_obj, Response):
                response = response_obj
            elif response_obj is not None:
                response = Response(status.HTTP_200_OK, response_obj)
            else:
                response = Response(status.HTTP_204_NO_CONTENT)

            # Pre-serialize filtering (eg filter complex objects into natively serializable types)
            response.cleaned_content = self.filter_response(response.raw_content)

        except ErrorResponse, exc:
            response = exc.response

        return self.final(request, response, *args, **kwargs)

    def options(self, request, *args, **kwargs):
        response_obj = {
            'name': self.get_name(),
            'description': self.get_description(),
            'renders': self._rendered_media_types,
            'parses': self._parsed_media_types,
        }
        form = self.get_bound_form()
        if form is not None:
            field_name_types = {}
            for name, field in form.fields.iteritems():
                field_name_types[name] = field.__class__.__name__
            response_obj['fields'] = field_name_types
        # Note 'ErrorResponse' is misleading, it's just any response
        # that should be rendered and returned immediately, without any
        # response filtering.
        raise ErrorResponse(status.HTTP_200_OK, response_obj)


class ModelView(View):
    """
    A RESTful view that maps to a model in the database.
    """
    resource = resources.ModelResource


class InstanceModelView(InstanceMixin, ReadModelMixin, UpdateModelMixin, DeleteModelMixin, ModelView):
    """
    A view which provides default operations for read/update/delete against a model instance.
    """
    _suffix = 'Instance'


class ListModelView(ListModelMixin, ModelView):
    """
    A view which provides default operations for list, against a model in the database.
    """
    _suffix = 'List'


class ListOrCreateModelView(ListModelMixin, CreateModelMixin, ModelView):
    """
    A view which provides default operations for list and create, against a model in the database.
    """
    _suffix = 'List'
