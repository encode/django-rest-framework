from __future__ import unicode_literals

import os
import tempfile
import unittest

from django.conf.urls import url
from django.http import HttpResponse
from django.test import override_settings

from rest_framework.compat import coreapi
from rest_framework.parsers import FileUploadParser
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.test import APITestCase, CoreAPIClient
from rest_framework.views import APIView


def get_schema():
    return coreapi.Document(
        url='https://api.example.com/',
        title='Example API',
        content={
            'simple_link': coreapi.Link('/example/', description='example link'),
            'headers': coreapi.Link('/headers/'),
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
                'multipart-body': coreapi.Link('/example/', action='post', encoding='multipart/form-data', fields=[
                    coreapi.Field(name='example', location='body')
                ]),
                'urlencoded': coreapi.Link('/example/', action='post', encoding='application/x-www-form-urlencoded', fields=[
                    coreapi.Field(name='example')
                ]),
                'urlencoded-body': coreapi.Link('/example/', action='post', encoding='application/x-www-form-urlencoded', fields=[
                    coreapi.Field(name='example', location='body')
                ]),
                'raw_upload': coreapi.Link('/upload/', action='post', encoding='application/octet-stream', fields=[
                    coreapi.Field(name='example', location='body')
                ]),
            },
            'response': {
                'download': coreapi.Link('/download/'),
                'text': coreapi.Link('/text/')
            }
        }
    )


def _iterlists(querydict):
    if hasattr(querydict, 'iterlists'):
        return querydict.iterlists()
    return querydict.lists()


def _get_query_params(request):
    # Return query params in a plain dict, using a list value if more
    # than one item is present for a given key.
    return {
        key: (value[0] if len(value) == 1 else value)
        for key, value in
        _iterlists(request.query_params)
    }


def _get_data(request):
    if not isinstance(request.data, dict):
        return request.data
    # Coerce multidict into regular dict, and remove files to
    # make assertions simpler.
    if hasattr(request.data, 'iterlists') or hasattr(request.data, 'lists'):
        # Use a list value if a QueryDict contains multiple items for a key.
        return {
            key: value[0] if len(value) == 1 else value
            for key, value in _iterlists(request.data)
            if key not in request.FILES
        }
    return {
        key: value
        for key, value in request.data.items()
        if key not in request.FILES
    }


def _get_files(request):
    if not request.FILES:
        return {}
    return {
        key: {'name': value.name, 'content': value.read()}
        for key, value in request.FILES.items()
    }


class SchemaView(APIView):
    renderer_classes = [CoreJSONRenderer]

    def get(self, request):
        schema = get_schema()
        return Response(schema)


class ListView(APIView):
    def get(self, request):
        return Response({
            'method': request.method,
            'query_params': _get_query_params(request)
        })

    def post(self, request):
        if request.content_type:
            content_type = request.content_type.split(';')[0]
        else:
            content_type = None

        return Response({
            'method': request.method,
            'query_params': _get_query_params(request),
            'data': _get_data(request),
            'files': _get_files(request),
            'content_type': content_type
        })


class DetailView(APIView):
    def get(self, request, id):
        return Response({
            'id': id,
            'method': request.method,
            'query_params': _get_query_params(request)
        })


class UploadView(APIView):
    parser_classes = [FileUploadParser]

    def post(self, request):
        return Response({
            'method': request.method,
            'files': _get_files(request),
            'content_type': request.content_type
        })


class DownloadView(APIView):
    def get(self, request):
        return HttpResponse('some file content', content_type='image/png')


class TextView(APIView):
    def get(self, request):
        return HttpResponse('123', content_type='text/plain')


class HeadersView(APIView):
    def get(self, request):
        headers = {
            key[5:].replace('_', '-'): value
            for key, value in request.META.items()
            if key.startswith('HTTP_')
        }
        return Response({
            'method': request.method,
            'headers': headers
        })


urlpatterns = [
    url(r'^$', SchemaView.as_view()),
    url(r'^example/$', ListView.as_view()),
    url(r'^example/(?P<id>[0-9]+)/$', DetailView.as_view()),
    url(r'^upload/$', UploadView.as_view()),
    url(r'^download/$', DownloadView.as_view()),
    url(r'^text/$', TextView.as_view()),
    url(r'^headers/$', HeadersView.as_view()),
]


@unittest.skipUnless(coreapi, 'coreapi not installed')
@override_settings(ROOT_URLCONF='tests.test_api_client')
class APIClientTests(APITestCase):
    def test_api_client(self):
        client = CoreAPIClient()
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
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'query'], params={'example': 123})
        expected = {
            'method': 'GET',
            'query_params': {'example': '123'}
        }
        assert data == expected

    def test_session_headers(self):
        client = CoreAPIClient()
        client.session.headers.update({'X-Custom-Header': 'foo'})
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['headers'])
        assert data['headers']['X-CUSTOM-HEADER'] == 'foo'

    def test_query_params_with_multiple_values(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'query'], params={'example': [1, 2, 3]})
        expected = {
            'method': 'GET',
            'query_params': {'example': ['1', '2', '3']}
        }
        assert data == expected

    def test_form_params(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'form'], params={'example': 123})
        expected = {
            'method': 'POST',
            'content_type': 'application/json',
            'query_params': {},
            'data': {'example': 123},
            'files': {}
        }
        assert data == expected

    def test_body_params(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'body'], params={'example': 123})
        expected = {
            'method': 'POST',
            'content_type': 'application/json',
            'query_params': {},
            'data': 123,
            'files': {}
        }
        assert data == expected

    def test_path_params(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['location', 'path'], params={'id': 123})
        expected = {
            'method': 'GET',
            'query_params': {},
            'id': '123'
        }
        assert data == expected

    def test_multipart_encoding(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        temp = tempfile.NamedTemporaryFile()
        temp.write(b'example file content')
        temp.flush()

        with open(temp.name, 'rb') as upload:
            name = os.path.basename(upload.name)
            data = client.action(schema, ['encoding', 'multipart'], params={'example': upload})

        expected = {
            'method': 'POST',
            'content_type': 'multipart/form-data',
            'query_params': {},
            'data': {},
            'files': {'example': {'name': name, 'content': 'example file content'}}
        }
        assert data == expected

    def test_multipart_encoding_no_file(self):
        # When no file is included, multipart encoding should still be used.
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        data = client.action(schema, ['encoding', 'multipart'], params={'example': 123})

        expected = {
            'method': 'POST',
            'content_type': 'multipart/form-data',
            'query_params': {},
            'data': {'example': '123'},
            'files': {}
        }
        assert data == expected

    def test_multipart_encoding_multiple_values(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        data = client.action(schema, ['encoding', 'multipart'], params={'example': [1, 2, 3]})

        expected = {
            'method': 'POST',
            'content_type': 'multipart/form-data',
            'query_params': {},
            'data': {'example': ['1', '2', '3']},
            'files': {}
        }
        assert data == expected

    def test_multipart_encoding_string_file_content(self):
        # Test for `coreapi.utils.File` support.
        from coreapi.utils import File

        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        example = File(name='example.txt', content='123')
        data = client.action(schema, ['encoding', 'multipart'], params={'example': example})

        expected = {
            'method': 'POST',
            'content_type': 'multipart/form-data',
            'query_params': {},
            'data': {},
            'files': {'example': {'name': 'example.txt', 'content': '123'}}
        }
        assert data == expected

    def test_multipart_encoding_in_body(self):
        from coreapi.utils import File

        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        example = {'foo': File(name='example.txt', content='123'), 'bar': 'abc'}
        data = client.action(schema, ['encoding', 'multipart-body'], params={'example': example})

        expected = {
            'method': 'POST',
            'content_type': 'multipart/form-data',
            'query_params': {},
            'data': {'bar': 'abc'},
            'files': {'foo': {'name': 'example.txt', 'content': '123'}}
        }
        assert data == expected

    # URLencoded

    def test_urlencoded_encoding(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['encoding', 'urlencoded'], params={'example': 123})
        expected = {
            'method': 'POST',
            'content_type': 'application/x-www-form-urlencoded',
            'query_params': {},
            'data': {'example': '123'},
            'files': {}
        }
        assert data == expected

    def test_urlencoded_encoding_multiple_values(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['encoding', 'urlencoded'], params={'example': [1, 2, 3]})
        expected = {
            'method': 'POST',
            'content_type': 'application/x-www-form-urlencoded',
            'query_params': {},
            'data': {'example': ['1', '2', '3']},
            'files': {}
        }
        assert data == expected

    def test_urlencoded_encoding_in_body(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')
        data = client.action(schema, ['encoding', 'urlencoded-body'], params={'example': {'foo': 123, 'bar': True}})
        expected = {
            'method': 'POST',
            'content_type': 'application/x-www-form-urlencoded',
            'query_params': {},
            'data': {'foo': '123', 'bar': 'true'},
            'files': {}
        }
        assert data == expected

    # Raw uploads

    def test_raw_upload(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        temp = tempfile.NamedTemporaryFile()
        temp.write(b'example file content')
        temp.flush()

        with open(temp.name, 'rb') as upload:
            name = os.path.basename(upload.name)
            data = client.action(schema, ['encoding', 'raw_upload'], params={'example': upload})

        expected = {
            'method': 'POST',
            'files': {'file': {'name': name, 'content': 'example file content'}},
            'content_type': 'application/octet-stream'
        }
        assert data == expected

    def test_raw_upload_string_file_content(self):
        from coreapi.utils import File

        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        example = File('example.txt', '123')
        data = client.action(schema, ['encoding', 'raw_upload'], params={'example': example})

        expected = {
            'method': 'POST',
            'files': {'file': {'name': 'example.txt', 'content': '123'}},
            'content_type': 'text/plain'
        }
        assert data == expected

    def test_raw_upload_explicit_content_type(self):
        from coreapi.utils import File

        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        example = File('example.txt', '123', 'text/html')
        data = client.action(schema, ['encoding', 'raw_upload'], params={'example': example})

        expected = {
            'method': 'POST',
            'files': {'file': {'name': 'example.txt', 'content': '123'}},
            'content_type': 'text/html'
        }
        assert data == expected

    # Responses

    def test_text_response(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        data = client.action(schema, ['response', 'text'])

        expected = '123'
        assert data == expected

    def test_download_response(self):
        client = CoreAPIClient()
        schema = client.get('http://api.example.com/')

        data = client.action(schema, ['response', 'download'])
        assert data.basename == 'download.png'
        assert data.read() == b'some file content'
