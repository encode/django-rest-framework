from django.core.management.base import BaseCommand

from rest_framework.compat import coreapi
from rest_framework.renderers import CoreJSONRenderer, OpenAPIRenderer
from rest_framework.settings import api_settings


class Command(BaseCommand):
    help = "Generates configured API schema for project."

    def add_arguments(self, parser):
        # TODO
        # SchemaGenerator allows passing:
        #
        # - title
        # - url
        # - description
        # - urlconf
        # - patterns
        #
        # Don't particularly want to pass these on the command-line.
        # conf file?
        #
        # Other options to consider:
        # - indent
        # - ...
        pass

    def handle(self, *args, **options):
        assert coreapi is not None, 'coreapi must be installed.'

        generator_class = api_settings.DEFAULT_SCHEMA_GENERATOR_CLASS()
        generator = generator_class()

        schema = generator.get_schema(request=None, public=True)

        renderer = self.get_renderer('openapi')
        output = renderer.render(schema)

        self.stdout.write(output)

    def get_renderer(self, format):
        return {
            'corejson': CoreJSONRenderer(),
            'openapi': OpenAPIRenderer()
        }
