from django.core.handlers.wsgi import STATUS_CODE_TEXT

__all__ =['NoContent', 'Response', ]



class NoContent(object):
    """Used to indicate no body in http response.
    (We cannot just use None, as that is a valid, serializable response object.)
    
    TODO: On relflection I'm going to get rid of this and just not support serailized 'None' responses.
    """
    pass


class Response(object):
    def __init__(self, status=200, content=NoContent, headers={}):
        self.status = status
        self.has_content_body = not content is NoContent             # TODO: remove and just use content
        self.raw_content = content      # content prior to filtering - TODO: remove and just use content
        self.cleaned_content = content  # content after filtering      TODO: remove and just use content
        self.headers = headers
 
    @property
    def status_text(self):
        """Return reason text corrosponding to our HTTP response status code.
        Provided for convienience."""
        return STATUS_CODE_TEXT.get(self.status, '')


class ResponseException(BaseException):
    def __init__(self, status, content=NoContent, headers={}):
        self.response = Response(status, content=content, headers=headers)
