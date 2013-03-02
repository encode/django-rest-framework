from __future__ import unicode_literals
from django.test.client import FakePayload, Client as _Client, RequestFactory as _RequestFactory
from django.test.client import MULTIPART_CONTENT
from rest_framework.compat import urlparse


class RequestFactory(_RequestFactory):

    def __init__(self, **defaults):
        super(RequestFactory, self).__init__(**defaults)

    def patch(self, path, data={}, content_type=MULTIPART_CONTENT,
            **extra):
        "Construct a PATCH request."

        patch_data = self._encode_data(data, content_type)

        parsed = urlparse.urlparse(path)
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


class Client(_Client, RequestFactory):
    def patch(self, path, data={}, content_type=MULTIPART_CONTENT,
              follow=False, **extra):
        """
        Send a resource to the server using PATCH.
        """
        response = super(Client, self).patch(path, data=data, content_type=content_type, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response
