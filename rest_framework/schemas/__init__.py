from .generators import SchemaGenerator
from .inspectors import AutoSchema, ManualSchema  # noqa


def get_schema_view(
        title=None, url=None, description=None, urlconf=None, renderer_classes=None,
        public=False, patterns=None, generator_class=SchemaGenerator):
    """
    Return a schema view.
    """
    # Avoid import cycle on APIView
    from .views import SchemaView
    generator = generator_class(
        title=title, url=url, description=description,
        urlconf=urlconf, patterns=patterns,
    )
    return SchemaView.as_view(
        renderer_classes=renderer_classes,
        schema_generator=generator,
        public=public,
    )
