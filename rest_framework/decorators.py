"""
The most important decorator in this module is `@api_view`, which is used
for writing function-based views with REST framework.

There are also various decorators for setting the API policies on function
based views, as well as the `@detail_route` and `@list_route` decorators, which are
used to annotate methods on viewsets that should be included by routers.
"""
from __future__ import unicode_literals

import types
import warnings

from django.utils import six

from rest_framework.views import APIView


def api_view(http_method_names=None, exclude_from_schema=False):
    """
    Decorator that converts a function-based view into an APIView subclass.
    Takes a list of allowed methods for the view as an argument.
    """
    http_method_names = ['GET'] if (http_method_names is None) else http_method_names

    def decorator(func):

        WrappedAPIView = type(
            six.PY3 and 'WrappedAPIView' or b'WrappedAPIView',
            (APIView,),
            {'__doc__': func.__doc__}
        )

        # Note, the above allows us to set the docstring.
        # It is the equivalent of:
        #
        #     class WrappedAPIView(APIView):
        #         pass
        #     WrappedAPIView.__doc__ = func.doc    <--- Not possible to do this

        # api_view applied without (method_names)
        assert not(isinstance(http_method_names, types.FunctionType)), \
            '@api_view missing list of allowed HTTP methods'

        # api_view applied with eg. string instead of list of strings
        assert isinstance(http_method_names, (list, tuple)), \
            '@api_view expected a list of strings, received %s' % type(http_method_names).__name__

        allowed_methods = set(http_method_names) | {'options'}
        WrappedAPIView.http_method_names = [method.lower() for method in allowed_methods]

        def handler(self, *args, **kwargs):
            return func(*args, **kwargs)

        for method in http_method_names:
            setattr(WrappedAPIView, method.lower(), handler)

        WrappedAPIView.__name__ = func.__name__
        WrappedAPIView.__module__ = func.__module__

        WrappedAPIView.renderer_classes = getattr(func, 'renderer_classes',
                                                  APIView.renderer_classes)

        WrappedAPIView.parser_classes = getattr(func, 'parser_classes',
                                                APIView.parser_classes)

        WrappedAPIView.authentication_classes = getattr(func, 'authentication_classes',
                                                        APIView.authentication_classes)

        WrappedAPIView.throttle_classes = getattr(func, 'throttle_classes',
                                                  APIView.throttle_classes)

        WrappedAPIView.permission_classes = getattr(func, 'permission_classes',
                                                    APIView.permission_classes)

        WrappedAPIView.schema = getattr(func, 'schema',
                                        APIView.schema)

        if exclude_from_schema:
            warnings.warn(
                "The `exclude_from_schema` argument to `api_view` is deprecated. "
                "Use the `schema` decorator instead, passing `None`.",
                DeprecationWarning
            )
            WrappedAPIView.exclude_from_schema = exclude_from_schema

        return WrappedAPIView.as_view()
    return decorator


def renderer_classes(renderer_classes):
    def decorator(func):
        func.renderer_classes = renderer_classes
        return func
    return decorator


def parser_classes(parser_classes):
    def decorator(func):
        func.parser_classes = parser_classes
        return func
    return decorator


def authentication_classes(authentication_classes):
    def decorator(func):
        func.authentication_classes = authentication_classes
        return func
    return decorator


def throttle_classes(throttle_classes):
    def decorator(func):
        func.throttle_classes = throttle_classes
        return func
    return decorator


def permission_classes(permission_classes):
    def decorator(func):
        func.permission_classes = permission_classes
        return func
    return decorator


def schema(view_inspector):
    def decorator(func):
        func.schema = view_inspector
        return func
    return decorator


def action(methods=None, detail=None, url_path=None, url_name=None, **kwargs):
    """
    Mark a ViewSet method as a routable action.

    Set the `detail` boolean to determine if this action should apply to
    instance/detail requests or collection/list requests.
    """
    methods = ['get'] if (methods is None) else methods
    methods = [method.lower() for method in methods]

    assert detail is not None, (
        "@action() missing required argument: 'detail'"
    )

    def decorator(func):
        func.bind_to_methods = methods
        func.detail = detail
        func.url_path = url_path if url_path else func.__name__
        func.url_name = url_name if url_name else func.__name__.replace('_', '-')
        func.kwargs = kwargs
        return func
    return decorator


def detail_route(methods=None, **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for detail requests.
    """
    warnings.warn(
        "`detail_route` is pending deprecation and will be removed in 3.10 in favor of "
        "`action`, which accepts a `detail` bool. Use `@action(detail=True)` instead.",
        PendingDeprecationWarning, stacklevel=2
    )

    def decorator(func):
        func = action(methods, detail=True, **kwargs)(func)
        if 'url_name' not in kwargs:
            func.url_name = func.url_path.replace('_', '-')
        return func
    return decorator


def list_route(methods=None, **kwargs):
    """
    Used to mark a method on a ViewSet that should be routed for list requests.
    """
    warnings.warn(
        "`list_route` is pending deprecation and will be removed in 3.10 in favor of "
        "`action`, which accepts a `detail` bool. Use `@action(detail=False)` instead.",
        PendingDeprecationWarning, stacklevel=2
    )

    def decorator(func):
        func = action(methods, detail=False, **kwargs)(func)
        if 'url_name' not in kwargs:
            func.url_name = func.url_path.replace('_', '-')
        return func
    return decorator
