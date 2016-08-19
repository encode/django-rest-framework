from __future__ import unicode_literals

import unittest

from django.conf.urls import url
from django.test import override_settings

from rest_framework.compat import coreapi
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.test import APITestCase, get_api_client
from rest_framework.views import APIView


def get_schema():
    return coreapi.Document(
        url='https://api.example.com/',
        title='Example API',
        content={
            'simple_link': coreapi.Link('/example/'),
            'query_params': coreapi.Link('/example/', fields=[
                coreapi.Field(name='example')
            ]),
            'form_params': coreapi.Link('/example/', action='post', fields=[
                coreapi.Field(name='example')
            ]),
            'body_params': coreapi.Link('/example/', action='post', fields=[
                coreapi.Field(name='example', location='body')
            ]),
            'path_params': coreapi.Link('/example/{id}', fields=[
                coreapi.Field(name='id', location='path')
            ]),
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
            'query_params': request.query_params,
            'data': request.data
        })

    def post(self, request):
        return Response({
            'method': request.method,
            'query_params': request.query_params,
            'data': request.data
        })


class DetailView(APIView):
    def get(self, request, id):
        return Response({
            'id': id,
            'method': request.method,
            'query_params': request.query_params,
            'data': request.data
        })


urlpatterns = [
    url(r'^$', SchemaView.as_view()),
    url(r'^example/$', ListView.as_view()),
    url(r'^example/(?P<id>[0-9]+)/$', DetailView.as_view())
]


@unittest.skipUnless(coreapi, 'coreapi not installed')
@override_settings(ROOT_URLCONF='tests.test_api_client')
class APIClientTests(APITestCase):
    def test_api_client(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        assert schema.title == 'Example API'
        data = client.action(schema, ['simple_link'])
        assert data == {'method': 'GET', 'query_params': {}, 'data': {}}

    def test_query_params(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        assert schema.title == 'Example API'
        data = client.action(schema, ['query_params'], params={'example': 123})
        assert data == {'method': 'GET', 'query_params': {'example': '123'}, 'data': {}}

    def test_form_params(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        assert schema.title == 'Example API'
        data = client.action(schema, ['form_params'], params={'example': 123})
        assert data == {'method': 'POST', 'query_params': {}, 'data': {'example': 123}}

    def test_body_params(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        assert schema.title == 'Example API'
        data = client.action(schema, ['body_params'], params={'example': 123})
        assert data == {'method': 'POST', 'query_params': {}, 'data': 123}

    def test_path_params(self):
        client = get_api_client()
        schema = client.get('http://api.example.com/')
        assert schema.title == 'Example API'
        data = client.action(schema, ['path_params'], params={'id': 123})
        assert data == {'method': 'GET', 'query_params': {}, 'data': {}, 'id': '123'}
