from django.core.management.base import BaseCommand

from rest_framework.compat import coreapi
from rest_framework.renderers import (
    CoreJSONRenderer, JSONOpenAPIRenderer, OpenAPIRenderer
)
from rest_framework.schemas.generators import SchemaGenerator
from rest_framework.settings import api_settings


class Command(BaseCommand):
    help = "Generates configured API schema for project."

    def add_arguments(self, parser):
        parser.add_argument('--title', dest="title", default=None, type=str)
        parser.add_argument('--url', dest="url", default=None, type=str)
        parser.add_argument('--description', dest="description", default=None, type=str)
        parser.add_argument('--format', dest="format", choices=['openapi', 'openapi-json', 'corejson'], default='openapi', type=str)

    def handle(self, *args, **options):
        assert coreapi is not None, 'coreapi must be installed.'

        generator = SchemaGenerator(
            url=options['url'],
            title=options['title'],
            description=options['description']
        )

        schema = generator.get_schema(request=None, public=True)

        renderer = self.get_renderer(options['format'])
        output = renderer.render(schema)

        self.stdout.write(output)

    def get_renderer(self, format):
        return {
            'corejson': CoreJSONRenderer(),
            'openapi': OpenAPIRenderer(),
            'openapi-json': JSONOpenAPIRenderer()
        }[format]
