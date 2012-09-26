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
from rest_framework import status, exceptions
from rest_framework.compat import View, apply_markdown
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.settings import api_settings


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


class APIView(View):
    settings = api_settings

    renderer_classes = api_settings.DEFAULT_RENDERERS
    parser_classes = api_settings.DEFAULT_PARSERS
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION
    throttle_classes = api_settings.DEFAULT_THROTTLES
    permission_classes = api_settings.DEFAULT_PERMISSIONS
    content_negotiation_class = api_settings.DEFAULT_CONTENT_NEGOTIATION

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Override the default :meth:`as_view` to store an instance of the view
        as an attribute on the callable function.  This allows us to discover
        information about the view when we do URL reverse lookups.
        """
        view = super(APIView, cls).as_view(**initkwargs)
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
            'Vary': 'Accept'
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
        Called if `request.method` does not corrospond to a handler method.
        """
        raise exceptions.MethodNotAllowed(request.method)

    def permission_denied(self, request):
        """
        If request is not permitted, determine what kind of exception to raise.
        """
        raise exceptions.PermissionDenied()

    def throttled(self, request, wait):
        """
        If request is throttled, determine what kind of exception to raise.
        """
        raise exceptions.Throttled(wait)

    def get_format_suffix(self, **kwargs):
        """
        Determine if the request includes a '.json' style format suffix
        """
        if self.settings.FORMAT_SUFFIX_KWARG:
            return kwargs.get(self.settings.FORMAT_SUFFIX_KWARG)

    def get_renderers(self, format=None):
        """
        Instantiates and returns the list of renderers that this view can use.
        """
        return [renderer(self) for renderer in self.renderer_classes]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission(self) for permission in self.permission_classes]

    def get_throttles(self):
        """
        Instantiates and returns the list of thottles that this view uses.
        """
        return [throttle(self) for throttle in self.throttle_classes]

    def perform_content_negotiation(self, request, force=False):
        """
        Determine which renderer and media type to use render the response.
        """
        renderers = self.get_renderers()
        conneg = self.content_negotiation_class()
        return conneg.negotiate(request, renderers, self.format, force)

    def check_permissions(self, request, obj=None):
        """
        Check if request should be permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(request, obj):
                self.permission_denied(request)

    def check_throttles(self, request):
        """
        Check if request should be throttled.
        """
        for throttle in self.get_throttles():
            if not throttle.allow_request(request):
                self.throttled(request, throttle.wait())

    def initialize_request(self, request, *args, **kargs):
        """
        Returns the initial request object.
        """
        return Request(request, parser_classes=self.parser_classes,
                       authentication_classes=self.authentication_classes)

    def initial(self, request, *args, **kwargs):
        """
        Runs anything that needs to occur prior to calling the method handlers.
        """
        self.format = self.get_format_suffix(**kwargs)
        self.check_permissions(request)
        self.check_throttles(request)
        self.renderer, self.accepted_media_type = self.perform_content_negotiation(request)

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Returns the final response object.
        """
        if isinstance(response, Response):
            if not getattr(self, 'renderer', None):
                self.renderer, self.accepted_media_type = self.perform_content_negotiation(request, force=True)
            response.renderer = self.renderer
            response.accepted_media_type = self.accepted_media_type

        for key, value in self.headers.items():
            response[key] = value

        return response

    def handle_exception(self, exc):
        """
        Handle any exception that occurs, by returning an appropriate response,
        or re-raising the error.
        """
        if isinstance(exc, exceptions.Throttled):
            # Throttle wait header
            self.headers['X-Throttle-Wait-Seconds'] = '%d' % exc.wait

        if isinstance(exc, exceptions.APIException):
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
        """
        `.dispatch()` is pretty much the same as Django's regular dispatch,
        but with extra hooks for startup, finalize, and exception handling.
        """
        request = self.initialize_request(request, *args, **kwargs)
        self.request = request
        self.args = args
        self.kwargs = kwargs
        self.headers = self.default_response_headers

        try:
            self.initial(request, *args, **kwargs)

            # Get the appropriate handler method
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(),
                                  self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed

            response = handler(request, *args, **kwargs)

        except Exception as exc:
            response = self.handle_exception(exc)

        self.response = self.finalize_response(request, response, *args, **kwargs)
        return self.response
