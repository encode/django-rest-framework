from django.core.management.base import BaseCommand

from rest_framework.renderers import CoreJSONRenderer
from rest_framework.schemas import SchemaGenerator


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

        renderer = CoreJSONRenderer()
        generator = SchemaGenerator()
        schema = generator.get_schema(request=None, public=True)

        rendered_schema = renderer.render(schema, renderer_context={}).decode('utf8')

        self.stdout.write(rendered_schema)
