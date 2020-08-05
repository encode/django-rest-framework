import warnings
from urllib.parse import urljoin

from rest_framework import serializers

from .openapi import AutoSchema, SchemaGenerator
from .utils import is_list_view


class AgidSchemaGenerator(SchemaGenerator):

    def get_info(self):
        # Title and version are required by openapi specification 3.x
        info = {
            'title': self.title or '',
            'version': self.version or '',
            'contact': getattr(self, 'contact', {}),
            'termsOfService': getattr(self, 'termsOfService', {}),
            'license': getattr(self, 'license', {}),
            'x-api-id': getattr(self, 'x-api-id', {}),
            'x-summary': getattr(self, 'x-summary', {}),
        }

        if self.description is not None:
            info['description'] = self.description

        return info

    def get_servers(self):
        servers = getattr(self, 'servers', {})
        return servers

    def get_tags(self):
        tags = getattr(self, 'tags', {})
        return tags

    def get_schema(self, request=None, public=False):
        """
        Generate a OpenAPI schema.
        """
        self._initialise_endpoints()
        components_schemas = {}

        # Iterate endpoints generating per method path operations.
        paths = {}
        _, view_endpoints = self._get_paths_and_endpoints(None if public else request)
        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue

            operation = view.schema.get_operation(path, method)
            components = view.schema.get_components(path, method)
            for k in components.keys():
                if k not in components_schemas:
                    continue
                if components_schemas[k] == components[k]:
                    continue
                warnings.warn('Schema component "{}" has been overriden with a different value.'.format(k))

            components_schemas.update(components)

            # Normalise path for any provided mount url.
            if path.startswith('/'):
                path = path[1:]

            # AGID - remove trailing / from urls
            if path.endswith('/'):
                path = path[:-1]

            path = urljoin(self.url or '/', path)

            paths.setdefault(path, {})
            paths[path][method.lower()] = operation

        self.check_duplicate_operation_id(paths)

        # Compile final schema.
        schema = {
            'openapi': '3.0.2',
            'info': self.get_info(),
            'tags': self.get_tags(),
            'servers': self.get_servers(),
            'paths': paths,

        }

        if len(components_schemas) > 0:
            schema['components'] = {
                'schemas': components_schemas
            }

        return schema


class AgidAutoSchema(AutoSchema):

    def get_responses(self, path, method):
        if method == 'DELETE':
            return {
                '204': {
                    'description': ''
                }
            }

        self.response_media_types = self.map_renderers(path, method)

        serializer = self.get_serializer(path, method)

        if not isinstance(serializer, serializers.Serializer):
            item_schema = {}
        else:
            item_schema = self._get_reference(serializer)

        if is_list_view(path, method, self.view):
            response_schema = {
                'type': 'object',
                'items': item_schema,
            }
            paginator = self.get_paginator()
            if paginator:
                response_schema = paginator.get_paginated_response_schema(response_schema)
        else:
            response_schema = item_schema
        status_code = '201' if method == 'POST' else '200'
        return {
            status_code: {
                'content': {
                    ct: {'schema': response_schema}
                    for ct in self.response_media_types
                },
                # description is a mandatory property,
                # https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#responseObject
                # TODO: put something meaningful into it
                'description': ""
            }
        }

    def get_tags(self, path, method):
        # If user have specified tags, use them.
        if self._tags:
            return self._tags

        # First element of a specific path could be valid tag. This is a fallback solution.
        # PUT, PATCH, GET(Retrieve), DELETE:        /user_profile/{id}/       tags = [user-profile]
        # POST, GET(List):                          /user_profile/            tags = [user-profile]
        if path.startswith('/'):
            path = path[1:]

        return [path.split('/')[0].replace('_', '-')]
