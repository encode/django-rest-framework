"""
The Response class in REST framework is similar to HTTPResponse, except that
it is initialized with unrendered data, instead of a pre-rendered string.

The appropriate renderer is called during Django's template response rendering.
"""
from __future__ import unicode_literals
import django
from django.core.handlers.wsgi import STATUS_CODE_TEXT
from django.template.response import SimpleTemplateResponse
from django.utils import six


class Response(SimpleTemplateResponse):
    """
    An HttpResponse that allows its data to be rendered into
    arbitrary media types.
    """
    # TODO: remove that once Django 1.3 isn't supported
    if django.VERSION >= (1, 4):
        rendering_attrs = SimpleTemplateResponse.rendering_attrs + ['_closable_objects']

    def __init__(self, data=None, status=None,
                 template_name=None, headers=None,
                 exception=False, content_type=None):
        """
        Alters the init arguments slightly.
        For example, drop 'template_name', and instead use 'data'.

        Setting 'renderer' and 'media_type' will typically be deferred,
        For example being set automatically by the `APIView`.
        """
        super(Response, self).__init__(None, status=status)
        self.data = data
        self.template_name = template_name
        self.exception = exception
        self.content_type = content_type

        if headers:
            for name, value in six.iteritems(headers):
                self[name] = value

    @property
    def rendered_content(self):
        renderer = getattr(self, 'accepted_renderer', None)
        media_type = getattr(self, 'accepted_media_type', None)
        context = getattr(self, 'renderer_context', None)

        assert renderer, ".accepted_renderer not set on Response"
        assert media_type, ".accepted_media_type not set on Response"
        assert context, ".renderer_context not set on Response"
        context['response'] = self

        charset = renderer.charset
        content_type = self.content_type

        if content_type is None and charset is not None:
            content_type = "{0}; charset={1}".format(media_type, charset)
        elif content_type is None:
            content_type = media_type
        self['Content-Type'] = content_type

        ret = renderer.render(self.data, media_type, context)
        if isinstance(ret, six.text_type):
            assert charset, (
                'renderer returned unicode, and did not specify '
                'a charset value.'
            )
            return bytes(ret.encode(charset))

        if not ret:
            del self['Content-Type']

        return ret

    @property
    def status_text(self):
        """
        Returns reason text corresponding to our HTTP response status code.
        Provided for convenience.
        """
        # TODO: Deprecate and use a template tag instead
        # TODO: Status code text for RFC 6585 status codes
        return STATUS_CODE_TEXT.get(self.status_code, '')

    def __getstate__(self):
        """
        Remove attributes from the response that shouldn't be cached
        """
        state = super(Response, self).__getstate__()
        for key in ('accepted_renderer', 'renderer_context', 'data'):
            if key in state:
                del state[key]
        return state
