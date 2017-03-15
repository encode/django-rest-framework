from django.conf.urls import include, url

from rest_framework.renderers import (
    CoreJSONRenderer, DocumentationRenderer, SchemaJSRenderer
)
from rest_framework.schemas import get_schema_view


def get_docs_view(title=None, description=None, schema_url=None, public=True, patterns=None):
    renderer_classes = [DocumentationRenderer, CoreJSONRenderer]

    return get_schema_view(
        title=title,
        url=schema_url,
        description=description,
        renderer_classes=renderer_classes,
        public=public,
        patterns=patterns,
    )


def get_schemajs_view(title=None, description=None, schema_url=None, public=True, patterns=None):
    renderer_classes = [SchemaJSRenderer]

    return get_schema_view(
        title=title,
        url=schema_url,
        description=description,
        renderer_classes=renderer_classes,
        public=public,
        patterns=patterns,
    )


def include_docs_urls(title=None, description=None, schema_url=None, public=True, patterns=None):
    docs_view = get_docs_view(
        title=title,
        description=description,
        schema_url=schema_url,
        public=public,
        patterns=patterns,
    )
    schema_js_view = get_schemajs_view(
        title=title,
        description=description,
        schema_url=schema_url,
        public=public,
        patterns=patterns,
    )
    urls = [
        url(r'^$', docs_view, name='docs-index'),
        url(r'^schema.js$', schema_js_view, name='schema-js')
    ]
    return include(urls, namespace='api-docs')
