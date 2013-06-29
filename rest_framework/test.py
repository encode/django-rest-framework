# -- coding: utf-8 --

# Note that we use `DjangoRequestFactory` and `DjangoClient` names in order
# to make it harder for the user to import the wrong thing without realizing.
from __future__ import unicode_literals
from django.conf import settings
from django.test.client import Client as DjangoClient
from django.test.client import ClientHandler
from rest_framework.compat import RequestFactory as DjangoRequestFactory
from rest_framework.compat import force_bytes_or_smart_bytes, six
from rest_framework.renderers import JSONRenderer, MultiPartRenderer


class APIRequestFactory(DjangoRequestFactory):
    renderer_classes = {
        'json': JSONRenderer,
        'multipart': MultiPartRenderer
    }
    default_format = 'multipart'

    def _encode_data(self, data, format=None, content_type=None):
        """
        Encode the data returning a two tuple of (bytes, content_type)
        """

        if not data:
            return ('', None)

        assert format is None or content_type is None, (
            'You may not set both `format` and `content_type`.'
        )

        if content_type:
            # Content type specified explicitly, treat data as a raw bytestring
            ret = force_bytes_or_smart_bytes(data, settings.DEFAULT_CHARSET)

        else:
            # Use format and render the data into a bytestring
            format = format or self.default_format
            renderer = self.renderer_classes[format]()
            ret = renderer.render(data)

            # Determine the content-type header from the renderer
            if ';' in renderer.media_type:
                content_type = renderer.media_type
            else:
                content_type = "{0}; charset={1}".format(
                    renderer.media_type, renderer.charset
                )

            # Coerce text to bytes if required.
            if isinstance(ret, six.text_type):
                ret = bytes(ret.encode(renderer.charset))

        return ret, content_type

    def post(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('POST', path, data, content_type, **extra)

    def put(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('PUT', path, data, content_type, **extra)

    def patch(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('PATCH', path, data, content_type, **extra)

    def delete(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('DELETE', path, data, content_type, **extra)

    def options(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('OPTIONS', path, data, content_type, **extra)


class ForceAuthClientHandler(ClientHandler):
    """
    A patched version of ClientHandler that can enforce authentication
    on the outgoing requests.
    """

    def __init__(self, *args, **kwargs):
        self._force_auth_user = None
        self._force_auth_token = None
        super(ForceAuthClientHandler, self).__init__(*args, **kwargs)

    def get_response(self, request):
        # This is the simplest place we can hook into to patch the
        # request object.
        request._force_auth_user = self._force_auth_user
        request._force_auth_token = self._force_auth_token
        return super(ForceAuthClientHandler, self).get_response(request)


class APIClient(APIRequestFactory, DjangoClient):
    def __init__(self, enforce_csrf_checks=False, **defaults):
        # Note that our super call skips Client.__init__
        # since we don't need to instantiate a regular ClientHandler
        super(DjangoClient, self).__init__(**defaults)
        self.handler = ForceAuthClientHandler(enforce_csrf_checks)
        self.exc_info = None
        self._credentials = {}

    def credentials(self, **kwargs):
        """
        Sets headers that will be used on every outgoing request.
        """
        self._credentials = kwargs

    def force_authenticate(self, user=None, token=None):
        """
        Forcibly authenticates outgoing requests with the given
        user and/or token.
        """
        self.handler._force_auth_user = user
        self.handler._force_auth_token = token

    def request(self, **request):
        # Ensure that any credentials set get added to every request.
        request.update(self._credentials)
        return super(APIClient, self).request(**request)
