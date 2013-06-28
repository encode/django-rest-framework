from rest_framework.compat import six, RequestFactory
from rest_framework.renderers import JSONRenderer, MultiPartRenderer


class APIRequestFactory(RequestFactory):
    renderer_classes = {
        'json': JSONRenderer,
        'form': MultiPartRenderer
    }
    default_format = 'form'

    def __init__(self, format=None, **defaults):
        self.format = format or self.default_format
        super(APIRequestFactory, self).__init__(**defaults)

    def _encode_data(self, data, format, content_type):
        if not data:
            return ('', None)

        format = format or self.format

        if content_type is None and data is not None:
            renderer = self.renderer_classes[format]()
            data = renderer.render(data)
            # Determine the content-type header
            if ';' in renderer.media_type:
                content_type = renderer.media_type
            else:
                content_type = "{0}; charset={1}".format(
                    renderer.media_type, renderer.charset
                )
            # Coerce text to bytes if required.
            if isinstance(data, six.text_type):
                data = bytes(data.encode(renderer.charset))

        return data, content_type

    def post(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('POST', path, data, content_type, **extra)

    def put(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('PUT', path, data, content_type, **extra)

    def patch(self, path, data=None, format=None, content_type=None, **extra):
        data, content_type = self._encode_data(data, format, content_type)
        return self.generic('PATCH', path, data, content_type, **extra)
