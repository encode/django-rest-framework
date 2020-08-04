"""
rest_framework.schemas

schemas:
    __init__.py
    generators.py   # Top-down schema generation
    inspectors.py   # Per-endpoint view introspection
    utils.py        # Shared helper functions
    views.py        # Houses `SchemaView`, `APIView` subclass.

We expose a minimal "public" API directly from `schemas`. This covers the
basic use-cases:

    from rest_framework.schemas import (
        AutoSchema,
        ManualSchema,
        get_schema_view,
        SchemaGenerator,
    )

Other access should target the submodules directly
"""
from rest_framework.settings import api_settings
api_settings.defaults['DEFAULT_SCHEMA_CLASS'] = \
    'rest_framework.schemas.openapi_agid.AgidAutoSchema'

from . import openapi_agid
#  from .openapi_agid import AgidAutoSchema, AgidSchemaGenerator  # noqa
from .inspectors import DefaultSchema  # noqa


def get_schema_view(
        title=None, url=None, description=None, urlconf=None, renderer_classes=None,
        public=False, patterns=None,
        authentication_classes=api_settings.DEFAULT_AUTHENTICATION_CLASSES,
        permission_classes=api_settings.DEFAULT_PERMISSION_CLASSES,
        version=None, **kwargs):
    """
    Return a schema view.
    """
    generator_class = openapi_agid.AgidSchemaGenerator

    generator = generator_class(
        title=title, url=url, description=description,
        urlconf=urlconf, patterns=patterns, version=version, **kwargs
    )

    # Avoid import cycle on APIView
    from .views import SchemaView
    return SchemaView.as_view(
        renderer_classes=renderer_classes,
        schema_generator=generator,
        public=public,
        authentication_classes=authentication_classes,
        permission_classes=permission_classes,
    )
