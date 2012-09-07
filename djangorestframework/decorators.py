from functools import wraps
from django.http import Http404
from django.utils.decorators import available_attrs
from django.core.exceptions import PermissionDenied
from djangorestframework import exceptions
from djangorestframework import status
from djangorestframework.response import Response
from djangorestframework.request import Request
from djangorestframework.settings import api_settings


def api_view(allowed_methods):
    """
    Decorator for function based views.

        @api_view(['GET', 'POST'])
        def my_view(request):
            # request will be an instance of `Request`
            # `Response` objects will have .request set automatically
            # APIException instances will be handled
    """
    allowed_methods = [method.upper() for method in allowed_methods]

    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def inner(request, *args, **kwargs):
            try:

                request = Request(request)

                if request.method not in allowed_methods:
                    raise exceptions.MethodNotAllowed(request.method)

                response = func(request, *args, **kwargs)

                if isinstance(response, Response):
                    response.request = request
                    if api_settings.FORMAT_SUFFIX_KWARG:
                        response.format = kwargs.get(api_settings.FORMAT_SUFFIX_KWARG, None)
                return response

            except exceptions.APIException as exc:
                return Response({'detail': exc.detail}, status=exc.status_code)

            except Http404 as exc:
                return Response({'detail': 'Not found'},
                                status=status.HTTP_404_NOT_FOUND)

            except PermissionDenied as exc:
                return Response({'detail': 'Permission denied'},
                                status=status.HTTP_403_FORBIDDEN)
        return inner
    return decorator
