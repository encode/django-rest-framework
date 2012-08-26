from djangorestframework import status


class ParseError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Malformed request'

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class PermissionDenied(Exception):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to access this resource'

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class MethodNotAllowed(Exception):
    status_code = status.HTTP_405_METHOD_NOT_ALLOWED
    default_detail = "Method '%s' not allowed"

    def __init__(self, method, detail):
        self.detail = (detail or self.default_detail) % method


class UnsupportedMediaType(Exception):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    default_detail = "Unsupported media type '%s' in request"

    def __init__(self, media_type, detail=None):
        self.detail = (detail or self.default_detail) % media_type

# class Throttled(Exception):
#     def __init__(self, detail):
#         self.detail = detail
