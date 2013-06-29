# -- coding: utf-8 --

# Note that we use `DjangoRequestFactory` and `DjangoClient` names in order
# to make it harder for the user to import the wrong thing without realizing.
from __future__ import unicode_literals
from django.conf import settings
from django.test.client import Client as DjangoClient
from rest_framework.compat import RequestFactory as DjangoRequestFactory
from rest_framework.compat import force_bytes_or_smart_bytes, six
from rest_framework.renderers import JSONRenderer, MultiPartRenderer


class APIRequestFactory(DjangoRequestFactory):
    renderer_classes = {
        'json': JSONRenderer,
        'form': MultiPartRenderer
    }
    default_format = 'form'

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


class APIClient(APIRequestFactory, DjangoClient):
    def __init__(self, *args, **kwargs):
        self._credentials = {}
        super(APIClient, self).__init__(*args, **kwargs)

    def credentials(self, **kwargs):
        self._credentials = kwargs

    def get(self, path, data={}, follow=False, **extra):
        extra.update(self._credentials)
        response = super(APIClient, self).get(path, data=data, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response

    def head(self, path, data={}, follow=False, **extra):
        extra.update(self._credentials)
        response = super(APIClient, self).head(path, data=data, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response

    def post(self, path, data=None, format=None, content_type=None, follow=False, **extra):
        extra.update(self._credentials)
        response = super(APIClient, self).post(path, data=data, format=format, content_type=content_type, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response

    def put(self, path, data=None, format=None, content_type=None, follow=False, **extra):
        extra.update(self._credentials)
        response = super(APIClient, self).post(path, data=data, format=format, content_type=content_type, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response

    def patch(self, path, data=None, format=None, content_type=None, follow=False, **extra):
        extra.update(self._credentials)
        response = super(APIClient, self).post(path, data=data, format=format, content_type=content_type, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response

    def delete(self, path, data=None, format=None, content_type=None, follow=False, **extra):
        extra.update(self._credentials)
        response = super(APIClient, self).post(path, data=data, format=format, content_type=content_type, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response

    def options(self, path, data=None, format=None, content_type=None, follow=False, **extra):
        extra.update(self._credentials)
        response = super(APIClient, self).post(path, data=data, format=format, content_type=content_type, **extra)
        if follow:
            response = self._handle_redirects(response, **extra)
        return response
