try:
    from unittest.mock import PropertyMock, patch
except ImportError:
    from mock import PropertyMock, patch

from django.core.management import call_command
from django.test import TestCase
from django.utils.six import StringIO

from .test_api_client import get_schema


class GenerateSchemaTests(TestCase):
    """Tests for management command generateeschema."""

    def test_WIP_should_raise_AssertionError_if_coreapi_is_not_installed(self):  # noqa
        m_coreapi = PropertyMock(return_value=None)
        with patch("rest_framework.management.commands.generateschema.coreapi",
                   new_callable=m_coreapi):
            with self.assertRaisesRegexp(
                    AssertionError, "coreapi must be installed"):
                call_command('generateschema')

    @patch('sys.stdout', new_callable=StringIO)
    @patch('rest_framework.management.commands.generateschema.SchemaGenerator')
    def test_WIP_should_call_SchemaGenerator_with_options(self, m_SchemaGenerator, m_stdout):  # noqa
        m_SchemaGenerator.return_value.get_schema.return_value = get_schema()

        call_command('generateschema', '--title=Example API',
                     '--url=http://api.example.com', '--description=Example')

        m_SchemaGenerator.assert_called_once_with(
            description='Example', title='Example API',
            url='http://api.example.com')

    @patch('sys.stdout', new_callable=StringIO)
    @patch('rest_framework.management.commands.generateschema.SchemaGenerator')
    def test_WIP_should_render_openapi_schema(self, m_SchemaGenerator, m_stdout):  # noqa
        m_SchemaGenerator.return_value.get_schema.return_value = get_schema()
        expected_stdout = """info:
  description: ''
  title: Example API
  version: ''
openapi: 3.0.0
paths:
  /download/:
    ? ''
    : operationId: response_download
      tags:
      - response
  /example/:
    ? ''
    : operationId: location_query
      tags:
      - location
    post:
      operationId: location_body
      tags:
      - location
  /example/{id}:
    ? ''
    : operationId: location_path
      parameters:
      - in: path
        name: id
      tags:
      - location
  /headers/:
    ? ''
    : operationId: headers
  /text/:
    ? ''
    : operationId: response_text
      tags:
      - response
  /upload/:
    post:
      operationId: encoding_raw_upload
      tags:
      - encoding
servers:
- url: https://api.example.com/
"""  # noqa

        call_command('generateschema', '--title=Example API',
                     '--url=http://api.example.com', '--description=Example')

        m_SchemaGenerator.assert_called_once_with(
            description='Example', title='Example API',
            url='http://api.example.com')
        self.assertEqual(expected_stdout, m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('rest_framework.management.commands.generateschema.SchemaGenerator')
    def test_WIP_should_render_openapi_json_schema(self, m_SchemaGenerator, m_stdout):  # noqa
        m_SchemaGenerator.return_value.get_schema.return_value = get_schema()
        expected_stdout = '''{
    "openapi": "3.0.0",
    "info": {
        "version": "",
        "title": "Example API",
        "description": ""
    },
    "servers": [
        {
            "url": "https://api.example.com/"
        }
    ],
    "paths": {
        "/example/": {
            "": {
                "operationId": "location_query",
                "tags": [
                    "location"
                ]
            },
            "post": {
                "operationId": "location_body",
                "tags": [
                    "location"
                ]
            }
        },
        "/headers/": {
            "": {
                "operationId": "headers"
            }
        },
        "/upload/": {
            "post": {
                "operationId": "encoding_raw_upload",
                "tags": [
                    "encoding"
                ]
            }
        },
        "/example/{id}": {
            "": {
                "operationId": "location_path",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path"
                    }
                ],
                "tags": [
                    "location"
                ]
            }
        },
        "/download/": {
            "": {
                "operationId": "response_download",
                "tags": [
                    "response"
                ]
            }
        },
        "/text/": {
            "": {
                "operationId": "response_text",
                "tags": [
                    "response"
                ]
            }
        }
    }
}
'''  # noqa

        call_command('generateschema', '--format=openapi-json')

        self.assertEqual(expected_stdout, m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    @patch('rest_framework.management.commands.generateschema.SchemaGenerator')
    def test_WIP_should_render_corejson_schema(self, m_SchemaGenerator, m_stdout):  # noqa
        m_SchemaGenerator.return_value.get_schema.return_value = get_schema()
        expected_stdout = '''{"_type":"document","_meta":{"url":"https://api.example.com/","title":"Example API"},"encoding":{"multipart":{"_type":"link","url":"/example/","action":"post","encoding":"multipart/form-data","fields":[{"name":"example"}]},"multipart-body":{"_type":"link","url":"/example/","action":"post","encoding":"multipart/form-data","fields":[{"name":"example","location":"body"}]},"urlencoded":{"_type":"link","url":"/example/","action":"post","encoding":"application/x-www-form-urlencoded","fields":[{"name":"example"}]},"urlencoded-body":{"_type":"link","url":"/example/","action":"post","encoding":"application/x-www-form-urlencoded","fields":[{"name":"example","location":"body"}]},"raw_upload":{"_type":"link","url":"/upload/","action":"post","encoding":"application/octet-stream","fields":[{"name":"example","location":"body"}]}},"location":{"form":{"_type":"link","url":"/example/","action":"post","fields":[{"name":"example"}]},"body":{"_type":"link","url":"/example/","action":"post","fields":[{"name":"example","location":"body"}]},"query":{"_type":"link","url":"/example/","fields":[{"name":"example","schema":{"_type":"string","title":"","description":"example field"}}]},"path":{"_type":"link","url":"/example/{id}","fields":[{"name":"id","location":"path"}]}},"response":{"download":{"_type":"link","url":"/download/"},"text":{"_type":"link","url":"/text/"}},"simple_link":{"_type":"link","url":"/example/","description":"example link"},"headers":{"_type":"link","url":"/headers/"}}
'''  # noqa

        call_command('generateschema', '--format=corejson')

        self.assertEqual(expected_stdout, m_stdout.getvalue())
