from django.test.client import RequestFactory, FakePayload
from django.test.client import MULTIPART_CONTENT
from urlparse import urlparse


class RequestFactory(RequestFactory):

    def __init__(self, **defaults):
        super(RequestFactory, self).__init__(**defaults)

    def patch(self, path, data={}, content_type=MULTIPART_CONTENT,
            **extra):
        "Construct a PATCH request."

        patch_data = self._encode_data(data, content_type)

        parsed = urlparse(path)
        r = {
            'CONTENT_LENGTH': len(patch_data),
            'CONTENT_TYPE':   content_type,
            'PATH_INFO':      self._get_path(parsed),
            'QUERY_STRING':   parsed[4],
            'REQUEST_METHOD': 'PATCH',
            'wsgi.input':     FakePayload(patch_data),
        }
        r.update(extra)
        return self.request(**r)
