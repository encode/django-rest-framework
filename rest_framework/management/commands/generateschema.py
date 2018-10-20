import argparse
import sys

from django.core.management.base import BaseCommand

from rest_framework.compat import coreapi
from rest_framework.renderers import (
    CoreJSONRenderer, JSONOpenAPIRenderer, OpenAPIRenderer
)
from rest_framework.schemas.generators import SchemaGenerator


class Command(BaseCommand):
    help = "Generates configured API schema for project."

    def add_arguments(self, parser):
        parser.add_argument(
            '--title',
            help='A short description of the application. CommonMark syntax '
            'MAY be used for rich text representation.')
        parser.add_argument(
            '--url',
            help='A URL to the target host. This URL supports Server '
            'Variables and MAY be relative, to indicate that the host '
            'location is relative to the location where the OpenAPI document '
            'is being served. Variable substitutions will be made when a '
            'variable is named in {brackets}.')
        parser.add_argument(
            '--description',
            help='An optional string describing the host designated by the '
            'URL. CommonMark syntax MAY be used for rich text representation.')
        parser.add_argument(
            '--format',
            choices=['openapi', 'openapi-json', 'corejson'], default='openapi',
            help='Output format.')
        parser.add_argument(
            'output',
            nargs='?', type=argparse.FileType('w'), default=sys.stdout,
            help='Path to output file. If not specified, output to stdout')

    def handle(self, *args, **options):
        assert coreapi is not None, 'coreapi must be installed.'

        generator = SchemaGenerator(
            url=options['url'],
            title=options['title'],
            description=options['description']
        )

        schema = generator.get_schema(request=None, public=True)

        renderer = self.get_renderer(options['format'])
        output = renderer.render(schema, renderer_context={})
        options['output'].write(output.decode('utf-8'))

    def get_renderer(self, format):
        return {
            'corejson': CoreJSONRenderer(),
            'openapi': OpenAPIRenderer(),
            'openapi-json': JSONOpenAPIRenderer()
        }[format]
