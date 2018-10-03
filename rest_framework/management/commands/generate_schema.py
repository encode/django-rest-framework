import urllib.parse as urlparse

from django.core.management.base import BaseCommand

from rest_framework.compat import coreapi, coreschema
from rest_framework.renderers import CoreJSONRenderer, JSONRenderer
from rest_framework.schemas.generators import OpenAPISchemaGenerator
from rest_framework.settings import api_settings
from rest_framework.utils import json


class OpenAPICodec:
    CLASS_TO_TYPENAME = {
        coreschema.Object: 'object',
        coreschema.Array: 'array',
        coreschema.Number: 'number',
        coreschema.Integer: 'integer',
        coreschema.String: 'string',
        coreschema.Boolean: 'boolean',
    }

    def get_schema(self, instance):
        schema = {}
        if instance.__class__ in self.CLASS_TO_TYPENAME:
            schema['type'] = self.CLASS_TO_TYPENAME[instance.__class__]
        schema['title'] = instance.title,
        schema['description'] = instance.description
        if hasattr(instance, 'enum'):
            schema['enum'] = instance.enum
        return schema

    def get_parameters(self, link):
        parameters = []
        for field in link.fields:
            if field.location not in ['path', 'query']:
                continue
            parameter = {
                'name': field.name,
                'in': field.location,
            }
            if field.required:
                parameter['required'] = True
            if field.description:
                parameter['description'] = field.description
            if field.schema:
                parameter['schema'] = self.get_schema(field.schema)
            parameters.append(parameter)
        return parameters

    def get_operation(self, link, name, tag):
        operation_id = "%s_%s" % (tag, name) if tag else name
        parameters = self.get_parameters(link)

        operation = {
            'operationId': operation_id,
        }
        if link.title:
            operation['summary'] = link.title
        if link.description:
            operation['description'] = link.description
        if parameters:
            operation['parameters'] = parameters
        if tag:
            operation['tags'] = [tag]
        return operation

    def get_paths(self, document):
        paths = {}

        tag = None
        for name, link in document.links.items():
            path = urlparse.urlparse(link.url).path
            method = link.action.lower()
            paths.setdefault(path, {})
            paths[path][method] = self.get_operation(link, name, tag=tag)

        for tag, section in document.data.items():
            for name, link in section.links.items():
                path = urlparse.urlparse(link.url).path
                method = link.action.lower()
                paths.setdefault(path, {})
                paths[path][method] = self.get_operation(link, name, tag=tag)

        return paths

    def encode(self, document):
        return json.dumps({
            'openapi': '3.0.0',
            'info': {
                'version': '',
                'title': document.title,
                'description': document.description
            },
            'servers': [{
                'url': document.url
            }],
            'paths': self.get_paths(document)
        }, indent=4)


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

        generator_class = self._get_generator_class()
        generator = generator_class()

        schema = generator.get_schema(request=None, public=True)
        codec = OpenAPICodec()
        output = codec.encode(schema)

        self.stdout.write(output)

    def _get_generator_class(self):
        return api_settings.DEFAULT_SCHEMA_GENERATOR_CLASS

    def _get_renderer(self, generator):
        if isinstance(generator, OpenAPISchemaGenerator):
            return JSONRenderer()
        else:
            return CoreJSONRenderer()
