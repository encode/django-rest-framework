"""Default handlers, configurable in settings"""

from rest_framework.response import Response
from rest_framework import exceptions
from rest_framework import status
from django.core.exceptions import PermissionDenied
from django.http import Http404


def handle_exception(view_instance, exc):
    """
    Default exception handler for APIView.

    Handle any exception that occurs, by returning an appropriate response,
    or re-raising the error.
    """
    if isinstance(exc, exceptions.Throttled):
        # Throttle wait header
        view_instance.headers['X-Throttle-Wait-Seconds'] = '%d' % exc.wait

    if isinstance(exc, (exceptions.NotAuthenticated,
                        exceptions.AuthenticationFailed)):
        # WWW-Authenticate header for 401 responses, else coerce to 403
        auth_header = view_instance.get_authenticate_header(
            view_instance.request)

        if auth_header:
            view_instance.headers['WWW-Authenticate'] = auth_header
        else:
            exc.status_code = status.HTTP_403_FORBIDDEN

    if isinstance(exc, exceptions.APIException):
        return Response(exc.data, status=exc.status_code,
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
