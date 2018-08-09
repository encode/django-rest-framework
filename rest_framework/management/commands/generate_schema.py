from django.core.management.base import BaseCommand

from rest_framework.renderers import CoreJSONRenderer, JSONRenderer
from rest_framework.schemas.generators import OpenAPISchemaGenerator
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
        generator_class = self._get_generator_class()
        generator = generator_class()

        schema = generator.get_schema(request=None, public=True)

        renderer = self._get_renderer(generator)
        rendered_schema = renderer.render(schema, renderer_context={}).decode('utf8')

        self.stdout.write(rendered_schema)

    def _get_generator_class(self):
        return api_settings.DEFAULT_SCHEMA_GENERATOR_CLASS

    def _get_renderer(self, generator):
        if isinstance(generator, OpenAPISchemaGenerator):
            return JSONRenderer()
        else:
            return CoreJSONRenderer()
