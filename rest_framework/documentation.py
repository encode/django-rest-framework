from rest_framework.renderers import DocumentationRenderer, CoreJSONRenderer
from rest_framework.schemas import get_schema_view


def get_docs_view(title=None, url=None, renderer_classes=None):
    if renderer_classes is None:
        renderer_classes = [DocumentationRenderer, CoreJSONRenderer]
    return get_schema_view(title, url, renderer_classes)
