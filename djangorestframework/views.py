"""
The :mod:`views` module provides the Views you will most probably
be subclassing in your implementation.

By setting or modifying class attributes on your view, you change it's predefined behaviour.
"""

import re
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.views.decorators.csrf import csrf_exempt

from djangorestframework.compat import View as DjangoView, apply_markdown
from djangorestframework.response import Response
from djangorestframework.request import Request
from djangorestframework import renderers, parsers, authentication, permissions, status, exceptions


__all__ = (
    'View',
    'ModelView',
    'InstanceModelView',
    'ListModelView',
    'ListOrCreateModelView'
)


def _remove_trailing_string(content, trailing):
    """
    Strip trailing component `trailing` from `content` if it exists.
    Used when generating names from view classes.
    """
    if content.endswith(trailing) and content != trailing:
        return content[:-len(trailing)]
    return content


def _remove_leading_indent(content):
    """
    Remove leading indent from a block of text.
    Used when generating descriptions from docstrings.
    """
    whitespace_counts = [len(line) - len(line.lstrip(' '))
                         for line in content.splitlines()[1:] if line.lstrip()]

    # unindent the content if needed
    if whitespace_counts:
        whitespace_pattern = '^' + (' ' * min(whitespace_counts))
        return re.sub(re.compile(whitespace_pattern, re.MULTILINE), '', content)
    return content


def _camelcase_to_spaces(content):
    """
    Translate 'CamelCaseNames' to 'Camel Case Names'.
    Used when generating names from view classes.
    """
    camelcase_boundry = '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))'
    return re.sub(camelcase_boundry, ' \\1', content).strip()


class View(DjangoView):
    """
    Handles incoming requests and maps them to REST operations.
    Performs request deserialization, response serialization, authentication and input validation.
    """

    renderers = renderers.DEFAULT_RENDERERS
    """
    List of renderer classes the view can serialize the response with, ordered by preference.
    """

    parsers = parsers.DEFAULT_PARSERS
    """
    List of parser classes the view can parse the request with.
    """

    authentication = (authentication.UserLoggedInAuthentication,
                      authentication.BasicAuthentication)
    """
    List of all authenticating methods to attempt.
    """

    permission_classes = (permissions.FullAnonAccess,)
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
        return [method.upper() for method in self.http_method_names
                if hasattr(self, method)]

    @property
    def default_response_headers(self):
        return {
            'Allow': ', '.join(self.allowed_methods),
            'Vary': 'Authenticate, Accept'
        }

    def get_name(self):
        """
        Return the resource or view class name for use as this view's name.
        Override to customize.
        """
        name = self.__class__.__name__
        name = _remove_trailing_string(name, 'View')
        return _camelcase_to_spaces(name)

    def get_description(self, html=False):
        """
        Return the resource or view docstring for use as this view's description.
        Override to customize.
        """
        description = self.__doc__ or ''
        description = _remove_leading_indent(description)
        if html:
            return self.markup_description(description)
        return description

    def markup_description(self, description):
        """
        Apply HTML markup to the description of this view.
        """
        if apply_markdown:
            description = apply_markdown(description)
        else:
            description = escape(description).replace('\n', '<br />')
        return mark_safe(description)

    def http_method_not_allowed(self, request, *args, **kwargs):
        """
        Return an HTTP 405 error if an operation is called which does not have
        a handler method.
        """
        raise exceptions.MethodNotAllowed(request.method)

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

    @property
    def _rendered_media_types(self):
        """
        Return an list of all the media types that this response can render.
        """
        return [renderer.media_type for renderer in self.renderers]

    @property
    def _rendered_formats(self):
        """
        Return a list of all the formats that this response can render.
        """
        return [renderer.format for renderer in self.renderers]

    @property
    def _default_renderer(self):
        """
        Return the response's default renderer class.
        """
        return self.renderers[0]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission(self) for permission in self.permission_classes]

    def check_permissions(self, user):
        """
        Check user permissions and either raise an ``ImmediateResponse`` or return.
        """
        for permission in self.get_permissions():
            permission.check_permission(user)

    def initial(self, request, *args, **kargs):
        """
        This method is a hook for any code that needs to run prior to
        anything else.
        Required if you want to do things like set `request.upload_handlers`
        before the authentication and dispatch handling is run.
        """
        pass

    def final(self, request, response, *args, **kargs):
        """
        This method is a hook for any code that needs to run after everything
        else in the view.
        Returns the final response object.
        """
        response.view = self
        response.request = request
        response.renderers = self.renderers
        for key, value in self.headers.items():
            response[key] = value
        return response

    def handle_exception(self, exc):
        """
        Handle any exception that occurs, by returning an appropriate response,
        or re-raising the error.
        """
        if isinstance(exc, exceptions.REST_FRAMEWORK_EXCEPTIONS):
            return Response({'detail': exc.detail}, status=exc.status_code)
        elif isinstance(exc, Http404):
            return Response({'detail': 'Not found'},
                            status=status.HTTP_404_NOT_FOUND)
        elif isinstance(exc, PermissionDenied):
            return Response({'detail': 'Permission denied'},
                            status=status.HTTP_403_FORBIDDEN)
        raise

    # Note: session based authentication is explicitly CSRF validated,
    # all other authentication is CSRF exempt.
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        request = Request(request, parsers=self.parsers, authentication=self.authentication)
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.headers = self.default_response_headers

        try:
            self.initial(request, *args, **kwargs)

            # check that user has the relevant permissions
            self.check_permissions(request.user)

            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response = handler(request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.final(request, response, *args, **kwargs)
        return self.response

    def options(self, request, *args, **kwargs):
        content = {
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
            content['fields'] = field_name_types
        raise Response(content, status=status.HTTP_200_OK)
