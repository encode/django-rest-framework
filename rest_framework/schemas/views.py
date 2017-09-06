from rest_framework import exceptions, renderers
from rest_framework.response import Response
from rest_framework.schemas.generators import SchemaGenerator
from rest_framework.settings import api_settings
from rest_framework.views import APIView


class SchemaView(APIView):
    _ignore_model_permissions = True
    exclude_from_schema = True
    renderer_classes = None
    schema_generator = None
    public = False

    def __init__(self, *args, **kwargs):
        super(SchemaView, self).__init__(*args, **kwargs)
        if self.renderer_classes is None:
            if renderers.BrowsableAPIRenderer in api_settings.DEFAULT_RENDERER_CLASSES:
                self.renderer_classes = [
                    renderers.CoreJSONRenderer,
                    renderers.BrowsableAPIRenderer,
                ]
            else:
                self.renderer_classes = [renderers.CoreJSONRenderer]

    def get(self, request, *args, **kwargs):
        schema = self.schema_generator.get_schema(request, self.public)
        if schema is None:
            raise exceptions.PermissionDenied()
        return Response(schema)


def get_schema_view(
        title=None, url=None, description=None, urlconf=None, renderer_classes=None,
        public=False, patterns=None, generator_class=SchemaGenerator):
    """
    Return a schema view.
    """
    generator = generator_class(
        title=title, url=url, description=description,
        urlconf=urlconf, patterns=patterns,
    )
    return SchemaView.as_view(
        renderer_classes=renderer_classes,
        schema_generator=generator,
        public=public,
    )
