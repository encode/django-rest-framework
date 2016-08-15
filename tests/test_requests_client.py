from __future__ import unicode_literals

from django.conf.urls import url
from django.test import override_settings

from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView


class Root(APIView):
    def get(self, request):
        return Response({
            'method': request.method,
            'query_params': request.query_params,
        })

    def post(self, request):
        files = {
            key: (value.name, value.read())
            for key, value in request.FILES.items()
        }
        post = request.POST
        json = None
        if request.META.get('CONTENT_TYPE') == 'application/json':
            json = request.data

        return Response({
            'method': request.method,
            'query_params': request.query_params,
            'POST': post,
            'FILES': files,
            'JSON': json
        })


class Headers(APIView):
    def get(self, request):
        headers = {
            key[5:]: value
            for key, value in request.META.items()
            if key.startswith('HTTP_')
        }
        return Response({
            'method': request.method,
            'headers': headers
        })


urlpatterns = [
    url(r'^$', Root.as_view()),
    url(r'^headers/$', Headers.as_view()),
]


@override_settings(ROOT_URLCONF='tests.test_requests_client')
class RequestsClientTests(APITestCase):
    def test_get_request(self):
        response = self.requests.get('/')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'GET',
            'query_params': {}
        }
        assert response.json() == expected

    def test_get_request_query_params_in_url(self):
        response = self.requests.get('/?key=value')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'GET',
            'query_params': {'key': 'value'}
        }
        assert response.json() == expected

    def test_get_request_query_params_by_kwarg(self):
        response = self.requests.get('/', params={'key': 'value'})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'GET',
            'query_params': {'key': 'value'}
        }
        assert response.json() == expected

    def test_get_with_headers(self):
        response = self.requests.get('/headers/', headers={'User-Agent': 'example'})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        headers = response.json()['headers']
        assert headers['USER-AGENT'] == 'example'

    def test_post_form_request(self):
        response = self.requests.post('/', data={'key': 'value'})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'POST',
            'query_params': {},
            'POST': {'key': 'value'},
            'FILES': {},
            'JSON': None
        }
        assert response.json() == expected

    def test_post_json_request(self):
        response = self.requests.post('/', json={'key': 'value'})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'POST',
            'query_params': {},
            'POST': {},
            'FILES': {},
            'JSON': {'key': 'value'}
        }
        assert response.json() == expected

    def test_post_multipart_request(self):
        files = {
            'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\n')
        }
        response = self.requests.post('/', files=files)
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'POST',
            'query_params': {},
            'FILES': {'file': ['report.csv', 'some,data,to,send\nanother,row,to,send\n']},
            'POST': {},
            'JSON': None
        }
        assert response.json() == expected

    # cookies/session auth
