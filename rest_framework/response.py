from __future__ import unicode_literals
from django.core.handlers.wsgi import STATUS_CODE_TEXT
from django.template.response import SimpleTemplateResponse
from rest_framework.compat import six


class Response(SimpleTemplateResponse):
    """
    An HttpResponse that allows it's data to be rendered into
    arbitrary media types.
    """

    def __init__(self, data=None, status=200,
                 template_name=None, headers=None,
                 exception=False):
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

        self['Content-Type'] = media_type
        return renderer.render(self.data, media_type, context)

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
