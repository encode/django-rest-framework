from django.core.management.base import BaseCommand

from rest_framework.compat import yaml
from rest_framework.schemas.openapi import SchemaGenerator
from rest_framework.utils import json


class Command(BaseCommand):
    help = "Generates configured API schema for project."

    def add_arguments(self, parser):
        parser.add_argument('--title', dest="title", default='', type=str)
        parser.add_argument('--url', dest="url", default=None, type=str)
        parser.add_argument('--description', dest="description", default=None, type=str)
        parser.add_argument('--format', dest="format", choices=['openapi', 'openapi-json'], default='openapi', type=str)

    def handle(self, *args, **options):
        generator = SchemaGenerator(
            url=options['url'],
            title=options['title'],
            description=options['description']
        )

        schema = generator.get_schema(request=None, public=True)

        # TODO: Handle via renderer? More options?
        if options['format'] == 'openapi':
            output = yaml.dump(schema, default_flow_style=False)
        else:
            output = json.dumps(schema, indent=2)

        self.stdout.write(output)
