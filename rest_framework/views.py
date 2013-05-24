"""
Provides an APIView class that is the base of all views in REST framework.
"""
from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.utils.datastructures import SortedDict
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, exceptions
from rest_framework.compat import View
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.utils.formatting import get_view_name, get_view_description


class APIView(View):
    settings = api_settings

    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    parser_classes = api_settings.DEFAULT_PARSER_CLASSES
    authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
    throttle_classes = api_settings.DEFAULT_THROTTLE_CLASSES
    permission_classes = api_settings.DEFAULT_PERMISSION_CLASSES
    content_negotiation_class = api_settings.DEFAULT_CONTENT_NEGOTIATION_CLASS

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Store the original class on the view function.

        This allows us to discover information about the view when we do URL
        reverse lookups.  Used for breadcrumb generation.
        """
        view = super(APIView, cls).as_view(**initkwargs)
        view.cls = cls
        return view

    @property
    def allowed_methods(self):
        """
        Wrap Django's private `_allowed_methods` interface in a public property.
        """
        return self._allowed_methods()

    @property
    def default_response_headers(self):
        # TODO: deprecate?
        # TODO: Only vary by accept if multiple renderers
        return {
            'Allow': ', '.join(self.allowed_methods),
            'Vary': 'Accept'
        }

    def http_method_not_allowed(self, request, *args, **kwargs):
        """
        If `request.method` does not correspond to a handler method,
        determine what kind of exception to raise.
        """
        raise exceptions.MethodNotAllowed(request.method)

    def permission_denied(self, request):
        """
        If request is not permitted, determine what kind of exception to raise.
        """
        if not self.request.successful_authenticator:
            raise exceptions.NotAuthenticated()
        raise exceptions.PermissionDenied()

    def throttled(self, request, wait):
        """
        If request is throttled, determine what kind of exception to raise.
        """
        raise exceptions.Throttled(wait)

    def get_authenticate_header(self, request):
        """
        If a request is unauthenticated, determine the WWW-Authenticate
        header to use for 401 responses, if any.
        """
        authenticators = self.get_authenticators()
        if authenticators:
            return authenticators[0].authenticate_header(request)

    def get_parser_context(self, http_request):
        """
        Returns a dict that is passed through to Parser.parse(),
        as the `parser_context` keyword argument.
        """
        # Note: Additionally `request` will also be added to the context
        #       by the Request object.
        return {
            'view': self,
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {})
        }

    def get_renderer_context(self):
        """
        Returns a dict that is passed through to Renderer.render(),
        as the `renderer_context` keyword argument.
        """
        # Note: Additionally 'response' will also be added to the context,
        #       by the Response object.
        return {
            'view': self,
            'args': getattr(self, 'args', ()),
            'kwargs': getattr(self, 'kwargs', {}),
            'request': getattr(self, 'request', None)
        }

    # API policy instantiation methods

    def get_format_suffix(self, **kwargs):
        """
        Determine if the request includes a '.json' style format suffix
        """
        if self.settings.FORMAT_SUFFIX_KWARG:
            return kwargs.get(self.settings.FORMAT_SUFFIX_KWARG)

    def get_renderers(self):
        """
        Instantiates and returns the list of renderers that this view can use.
        """
        return [renderer() for renderer in self.renderer_classes]

    def get_parsers(self):
        """
        Instantiates and returns the list of parsers that this view can use.
        """
        return [parser() for parser in self.parser_classes]

    def get_authenticators(self):
        """
        Instantiates and returns the list of authenticators that this view can use.
        """
        return [auth() for auth in self.authentication_classes]

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        return [permission() for permission in self.permission_classes]

    def get_throttles(self):
        """
        Instantiates and returns the list of throttles that this view uses.
        """
        return [throttle() for throttle in self.throttle_classes]

    def get_content_negotiator(self):
        """
        Instantiate and return the content negotiation class to use.
        """
        if not getattr(self, '_negotiator', None):
            self._negotiator = self.content_negotiation_class()
        return self._negotiator

    # API policy implementation methods

    def perform_content_negotiation(self, request, force=False):
        """
        Determine which renderer and media type to use render the response.
        """
        renderers = self.get_renderers()
        conneg = self.get_content_negotiator()

        try:
            return conneg.select_renderer(request, renderers, self.format_kwarg)
        except Exception:
            if force:
                return (renderers[0], renderers[0].media_type)
            raise

    def perform_authentication(self, request):
        """
        Perform authentication on the incoming request.

        Note that if you override this and simply 'pass', then authentication
        will instead be performed lazily, the first time either
        `request.user` or `request.auth` is accessed.
        """
        request.user

    def check_permissions(self, request):
        """
        Check if the request should be permitted.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                self.permission_denied(request)

    def check_object_permissions(self, request, obj):
        """
        Check if the request should be permitted for a given object.
        Raises an appropriate exception if the request is not permitted.
        """
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(request)

    def check_throttles(self, request):
        """
        Check if request should be throttled.
        Raises an appropriate exception if the request is throttled.
        """
        for throttle in self.get_throttles():
            if not throttle.allow_request(request, self):
                self.throttled(request, throttle.wait())

    # Dispatch methods

    def initialize_request(self, request, *args, **kargs):
        """
        Returns the initial request object.
        """
        parser_context = self.get_parser_context(request)

        return Request(request,
                       parsers=self.get_parsers(),
                       authenticators=self.get_authenticators(),
                       negotiator=self.get_content_negotiator(),
                       parser_context=parser_context)

    def initial(self, request, *args, **kwargs):
        """
        Runs anything that needs to occur prior to calling the method handler.
        """
        self.format_kwarg = self.get_format_suffix(**kwargs)

        # Ensure that the incoming request is permitted
        self.perform_authentication(request)
        self.check_permissions(request)
        self.check_throttles(request)

        # Perform content negotiation and store the accepted info on the request
        neg = self.perform_content_negotiation(request)
        request.accepted_renderer, request.accepted_media_type = neg

    def finalize_response(self, request, response, *args, **kwargs):
        """
        Returns the final response object.
        """
        # Make the error obvious if a proper response is not returned
        assert isinstance(response, HttpResponse), (
            'Expected a `Response` to be returned from the view, '
            'but received a `%s`' % type(response)
        )

        if isinstance(response, Response):
            if not getattr(request, 'accepted_renderer', None):
                neg = self.perform_content_negotiation(request, force=True)
                request.accepted_renderer, request.accepted_media_type = neg

            response.accepted_renderer = request.accepted_renderer
            response.accepted_media_type = request.accepted_media_type
            response.renderer_context = self.get_renderer_context()

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

        if isinstance(exc, (exceptions.NotAuthenticated,
                            exceptions.AuthenticationFailed)):
            # WWW-Authenticate header for 401 responses, else coerce to 403
            auth_header = self.get_authenticate_header(self.request)

            if auth_header:
                self.headers['WWW-Authenticate'] = auth_header
            else:
                exc.status_code = status.HTTP_403_FORBIDDEN

        if isinstance(exc, exceptions.APIException):
            return Response({'detail': exc.detail},
                            status=exc.status_code,
                            exception=True)
        elif isinstance(exc, Http404):
            return Response({'detail': 'Not found'},
                            status=status.HTTP_404_NOT_FOUND,
                            exception=True)
        elif isinstance(exc, PermissionDenied):
            return Response({'detail': 'Permission denied'},
                            status=status.HTTP_403_FORBIDDEN,
                            exception=True)
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
        self.headers = self.default_response_headers  # deprecate?

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

    def options(self, request, *args, **kwargs):
        """
        Handler method for HTTP 'OPTIONS' request.
        We may as well implement this as Django will otherwise provide
        a less useful default implementation.
        """
        return Response(self.metadata(request), status=status.HTTP_200_OK)

    def metadata(self, request):
        """
        Return a dictionary of metadata about the view.
        Used to return responses for OPTIONS requests.
        """
        ret = SortedDict()
        ret['name'] = get_view_name(self.__class__)
        ret['description'] = get_view_description(self.__class__)
        ret['renders'] = [renderer.media_type for renderer in self.renderer_classes]
        ret['parses'] = [parser.media_type for parser in self.parser_classes]
        return ret
