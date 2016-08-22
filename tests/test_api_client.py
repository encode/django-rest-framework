from __future__ import unicode_literals

import os
import tempfile
import unittest

from django.conf.urls import url
from django.test import override_settings

from rest_framework.compat import coreapi
from rest_framework.parsers import FileUploadParser
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.test import APITestCase, get_api_client
from rest_framework.views import APIView


def get_schema():
    return coreapi.Document(
        url='https://api.example.com/',
        title='Example API',
        content={
            'simple_link': coreapi.Link('/example/', description='example link'),
            'location': {
                'query': coreapi.Link('/example/', fields=[
                    coreapi.Field(name='example', description='example field')
                ]),
                'form': coreapi.Link('/example/', action='post', fields=[
                    coreapi.Field(name='example'),
                ]),
                'body': coreapi.Link('/example/', action='post', fields=[
                    coreapi.Field(name='example', location='body')
                ]),
                'path': coreapi.Link('/example/{id}', fields=[
                    coreapi.Field(name='id', location='path')
                ])
            },
            'encoding': {
                'multipart': coreapi.Link('/example/', action='post', encoding='multipart/form-data', fields=[
                    coreapi.Field(name='example')
                ]),
                'urlencoded': coreapi.Link('/example/', action='post', encoding='application/x-www-form-urlencoded', fields=[
                    coreapi.Field(name='example')
                ]),
                'raw_upload': coreapi.Link('/upload/', action='post', encoding='application/octet-stream', fields=[
                    coreapi.Field(name='example', location='body')
                ]),
            }
        }
    )


class SchemaView(APIView):
    renderer_classes = [CoreJSONRenderer]

    def get(self, request):
        schema = get_schema()
        return Response(schema)


class ListView(APIView):
    def get(self, request):
        return Response({
            'method': request.method,
            'query_params': request.query_params
        })

    def post(self, request):
        if request.content_type:
            content_type = request.content_type.split(';')[0]
        else:
            content_type = None

        if isinstance(request.data, dict):
            # Coerce multidict into regular dict, and remove files to
            # make assertions simpler.
            data = {
                key: value for key, value in request.data.items()
                if key not in request.FILES
            }
        else:
            data = request.data

        if request.FILES:
            files = {
                key: {'name': value.name, 'contents': value.read()}
                for key, value in request.FILES.items()
            }
        else:
            files = None

        return Response({
            'method': request.method,
            'query_params': request.query_params,
            'data': data,
            'files': files,
            'content_type': content_type
        })


class DetailView(APIView):
    def get(self, request, id):
        return Response({
            'id': id,
            'method': request.method,
            'query_params': request.query_params
        })


class UploadView(APIView):
    parser_classes = [FileUploadParser]

    def post(self, request):
        upload = request.data['file']
        contents = upload.read()
        return Response({
            'method': request.method,
            'files': {'name': upload.name, 'contents': contents}
        })


urlpatterns = [
    url(r'^$', SchemaView.as_view()),
    url(r'^example/$', ListView.as_view()),
    url(r'^example/(?P<id>[0-9]+)/$', DetailView.as_view()),
    url(r'^upload/$', UploadView.as_view()),
]


@unittest.skipUnless(coreapi, 'coreapi not installed')
@override_settings(ROOT_URLCONF='tests.test_api_client')
class APIClientTests(APITestCase):
    def test_api_client(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        assert schema.title == 'Example API'
        assert schema.url == 'https://api.example.com/'
        assert schema['simple_link'].description == 'example link'
        assert schema['location']['query'].fields[0].description == 'example field'
        data = client.action(schema, ['simple_link'])
        expected = {
            'method': 'GET',
            'query_params': {}
        }
        assert data == expected

    def test_query_params(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'query'], params={'example': 123})
        expected = {
            'method': 'GET',
            'query_params': {'example': '123'}
        }
        assert data == expected

    def test_form_params(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'form'], params={'example': 123})
        expected = {
            'method': 'POST',
            'content_type': 'application/json',
            'query_params': {},
            'data': {'example': 123},
            'files': None
        }
        assert data == expected

    def test_body_params(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'body'], params={'example': 123})
        expected = {
            'method': 'POST',
            'content_type': 'application/json',
            'query_params': {},
            'data': 123,
            'files': None
        }
        assert data == expected

    def test_path_params(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'path'], params={'id': 123})
        expected = {
            'method': 'GET',
            'query_params': {},
            'id': '123'
        }
        assert data == expected

    def test_multipart_encoding(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')

        temp = tempfile.NamedTemporaryFile()
        temp.write('example file contents')
        temp.flush()

        with open(temp.name, 'rb') as upload:
            name = os.path.basename(upload.name)
            data = client.action(schema, ['encoding', 'multipart'], params={'example': upload})

        expected = {
            'method': 'POST',
            'content_type': 'multipart/form-data',
            'query_params': {},
            'data': {},
            'files': {'example': {'name': name, 'contents': 'example file contents'}}
        }
        assert data == expected

    def test_urlencoded_encoding(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['encoding', 'urlencoded'], params={'example': 123})
        expected = {
            'method': 'POST',
            'content_type': 'application/x-www-form-urlencoded',
            'query_params': {},
            'data': {'example': '123'},
            'files': None
        }
        assert data == expected

    def test_raw_upload(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')

        temp = tempfile.NamedTemporaryFile()
        temp.write('example file contents')
        temp.flush()

        with open(temp.name, 'rb') as upload:
            name = os.path.basename(upload.name)
            data = client.action(schema, ['encoding', 'raw_upload'], params={'example': upload})

        expected = {
            'method': 'POST',
            'files': {'name': name, 'contents': 'example file contents'}
        }
        assert data == expected
