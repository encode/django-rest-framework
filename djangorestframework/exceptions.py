from djangorestframework import status


class ParseError(Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Malformed request'

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


class PermissionDenied(Exception):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to access this resource.'

    def __init__(self, detail=None):
        self.detail = detail or self.default_detail


# class Throttled(Exception):
#     def __init__(self, detail):
#         self.detail = detail
