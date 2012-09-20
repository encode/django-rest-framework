from django.template.response import SimpleTemplateResponse
from django.core.handlers.wsgi import STATUS_CODE_TEXT


class Response(SimpleTemplateResponse):
    """
    An HttpResponse that allows it's data to be rendered into
    arbitrary media types.
    """

    def __init__(self, data=None, status=None, headers=None,
                 renderer=None, media_type=None):
        """
        Alters the init arguments slightly.
        For example, drop 'template_name', and instead use 'data'.

        Setting 'renderer' and 'media_type' will typically be defered,
        For example being set automatically by the `APIView`.
        """
        super(Response, self).__init__(None, status=status)
        self.data = data
        self.headers = headers and headers[:] or []
        self.renderer = renderer
        self.media_type = media_type

    @property
    def rendered_content(self):
        self['Content-Type'] = self.renderer.media_type
        if self.data is None:
            return self.renderer.render()
        return self.renderer.render(self.data, self.media_type)

    @property
    def status_text(self):
        """
        Returns reason text corresponding to our HTTP response status code.
        Provided for convenience.
        """
        return STATUS_CODE_TEXT.get(self.status_code, '')
