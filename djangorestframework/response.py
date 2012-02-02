"""
The :mod:`response` module provides Response classes you can use in your
views to return a certain HTTP response. Typically a response is *rendered*
into a HTTP response depending on what renderers are set on your view and
als depending on the accept header of the request.
"""

from django.core.handlers.wsgi import STATUS_CODE_TEXT

__all__ = ('Response', 'ErrorResponse')

# TODO: remove raw_content/cleaned_content and just use content?


class Response(object):
    """
    An HttpResponse that may include content that hasn't yet been serialized.
    """

    def __init__(self, status=200, content=None, headers=None):
        self.status = status
        self.media_type = None
        self.has_content_body = content is not None
        self.raw_content = content      # content prior to filtering
        self.cleaned_content = content  # content after filtering
        self.headers = headers or {}

    @property
    def status_text(self):
        """
        Return reason text corresponding to our HTTP response status code.
        Provided for convenience.
        """
        return STATUS_CODE_TEXT.get(self.status, '')


class ErrorResponse(Exception):
    """
    An exception representing an Response that should be returned immediately.
    Any content should be serialized as-is, without being filtered.
    """

    def __init__(self, status, content=None, headers={}):
        self.response = Response(status, content=content, headers=headers)
