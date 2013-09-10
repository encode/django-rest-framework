# -- coding: utf-8 --

# Note that we import as `DjangoRequestFactory` and `DjangoClient` in order
# to make it harder for the user to import the wrong thing without realizing.
from __future__ import unicode_literals
import django
from django.conf import settings
from django.test.client import Client as DjangoClient
from django.test.client import ClientHandler
from django.test import testcases
from rest_framework.settings import api_settings
from rest_framework.compat import RequestFactory as DjangoRequestFactory
from rest_framework.compat import force_bytes_or_smart_bytes, six


def force_authenticate(request, user=None, token=None):
    request._force_auth_user = user
    request._force_auth_token = token


class APIRequestFactory(DjangoRequestFactory):
    renderer_classes_list = api_settings.TEST_REQUEST_RENDERER_CLASSES
    default_format = api_settings.TEST_REQUEST_DEFAULT_FORMAT

    def __init__(self, enforce_csrf_checks=False, **defaults):
        self.enforce_csrf_checks = enforce_csrf_checks
        self.renderer_classes = {}
        for cls in self.renderer_classes_list:
            self.renderer_classes[cls.format] = cls
        super(APIRequestFactory, self).__init__(**defaults)

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
            format = format or self.default_format

            assert format in self.renderer_classes, ("Invalid format '{0}'. "
                "Available formats are {1}.  Set TEST_REQUEST_RENDERER_CLASSES "
                "to enable extra request formats.".format(
                    format,
                    ', '.join(["'" + fmt + "'" for fmt in self.renderer_classes.keys()])
                )
            )

            # Use format and render the data into a bytestring
            renderer = self.renderer_classes[format]()
            ret = renderer.render(data)

            # Determine the content-type header from the renderer
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

    def request(self, **kwargs):
        request = super(APIRequestFactory, self).request(**kwargs)
        request._dont_enforce_csrf_checks = not self.enforce_csrf_checks
        return request


class ForceAuthClientHandler(ClientHandler):
    """
    A patched version of ClientHandler that can enforce authentication
    on the outgoing requests.
    """

    def __init__(self, *args, **kwargs):
        self._force_user = None
        self._force_token = None
        super(ForceAuthClientHandler, self).__init__(*args, **kwargs)

    def get_response(self, request):
        # This is the simplest place we can hook into to patch the
        # request object.
        force_authenticate(request, self._force_user, self._force_token)
        return super(ForceAuthClientHandler, self).get_response(request)


class APIClient(APIRequestFactory, DjangoClient):
    def __init__(self, enforce_csrf_checks=False, **defaults):
        super(APIClient, self).__init__(**defaults)
        self.handler = ForceAuthClientHandler(enforce_csrf_checks)
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
        self.handler._force_user = user
        self.handler._force_token = token
        if user is None:
            self.logout()  # Also clear any possible session info if required

    def request(self, **kwargs):
        # Ensure that any credentials set get added to every request.
        kwargs.update(self._credentials)
        return super(APIClient, self).request(**kwargs)


class APITransactionTestCase(testcases.TransactionTestCase):
    client_class = APIClient


class APITestCase(testcases.TestCase):
    client_class = APIClient


if django.VERSION >= (1, 4):
    class APISimpleTestCase(testcases.SimpleTestCase):
        client_class = APIClient

    class APILiveServerTestCase(testcases.LiveServerTestCase):
        client_class = APIClient
