"""
Handled exceptions raised by REST framework.

In addition Django's built in 403 and 404 exceptions are handled.
(`django.http.Http404` and `django.core.exceptions.PermissionDenied`)
"""
from __future__ import unicode_literals
from rest_framework import status
import math


class APIException(Exception):
    """
    Base class for REST framework exceptions.
    Subclasses should provide `.status_code` and `.default_detail` properties.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = ''

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail

    def __str__(self):
        return self.detail

class ParseError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Malformed request.'


class AuthenticationFailed(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Incorrect authentication credentials.'


class NotAuthenticated(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Authentication credentials were not provided.'


class PermissionDenied(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'


class MethodNotAllowed(APIException):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = "Method '%s' not allowed."

    def __init__(self, method, detail=None):
        self.detail = (detail or self.default_detail) % method


class NotAcceptable(APIException):
    status_code = status.HTTP_406_NOT_ACCEPTABLE
    default_detail = "Could not satisfy the request's Accept header"

    def __init__(self, detail=None, available_renderers=None):
        self.detail = detail or self.default_detail
        self.available_renderers = available_renderers


class UnsupportedMediaType(APIException):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = "Unsupported media type '%s' in request."

    def __init__(self, media_type, detail=None):
        self.detail = (detail or self.default_detail) % media_type


class Throttled(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Request was throttled.'
    extra_detail = "Expected available in %d second%s."

    def __init__(self, wait=None, detail=None):
        if wait is None:
            self.detail = detail or self.default_detail
            self.wait = None
        else:
            format = (detail or self.default_detail) + self.extra_detail
            self.detail = format % (wait, wait != 1 and 's' or '')
            self.wait = math.ceil(wait)
