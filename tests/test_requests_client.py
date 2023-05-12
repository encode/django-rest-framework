import unittest

from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.test import override_settings
from django.urls import path
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

from rest_framework.compat import requests
from rest_framework.response import Response
from rest_framework.test import APITestCase, RequestsClient
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


class SessionView(APIView):
    def get(self, request):
        return Response({
            key: value for key, value in request.session.items()
        })

    def post(self, request):
        for key, value in request.data.items():
            request.session[key] = value
        return Response({
            key: value for key, value in request.session.items()
        })


class AuthView(APIView):
    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        if request.user.is_authenticated:
            username = request.user.username
        else:
            username = None
        return Response({
            'username': username
        })

    @method_decorator(csrf_protect)
    def post(self, request):
        username = request.data['username']
        password = request.data['password']
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'error': 'incorrect credentials'})
        login(request, user)
        return redirect('/auth/')


urlpatterns = [
    path('', Root.as_view(), name='root'),
    path('headers/', HeadersView.as_view(), name='headers'),
    path('session/', SessionView.as_view(), name='session'),
    path('auth/', AuthView.as_view(), name='auth'),
]


@unittest.skipUnless(requests, 'requests not installed')
@override_settings(ROOT_URLCONF='tests.test_requests_client')
class RequestsClientTests(APITestCase):
    def test_get_request(self):
        client = RequestsClient()
        response = client.get('http://testserver/')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'GET',
            'query_params': {}
        }
        assert response.json() == expected

    def test_get_request_query_params_in_url(self):
        client = RequestsClient()
        response = client.get('http://testserver/?key=value')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'GET',
            'query_params': {'key': 'value'}
        }
        assert response.json() == expected

    def test_get_request_query_params_by_kwarg(self):
        client = RequestsClient()
        response = client.get('http://testserver/', params={'key': 'value'})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'method': 'GET',
            'query_params': {'key': 'value'}
        }
        assert response.json() == expected

    def test_get_with_headers(self):
        client = RequestsClient()
        response = client.get('http://testserver/headers/', headers={'User-Agent': 'example'})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        headers = response.json()['headers']
        assert headers['USER-AGENT'] == 'example'

    def test_get_with_session_headers(self):
        client = RequestsClient()
        client.headers.update({'User-Agent': 'example'})
        response = client.get('http://testserver/headers/')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        headers = response.json()['headers']
        assert headers['USER-AGENT'] == 'example'

    def test_post_form_request(self):
        client = RequestsClient()
        response = client.post('http://testserver/', data={'key': 'value'})
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
        client = RequestsClient()
        response = client.post('http://testserver/', json={'key': 'value'})
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
        client = RequestsClient()
        files = {
            'file': ('report.csv', 'some,data,to,send\nanother,row,to,send\n')
        }
        response = client.post('http://testserver/', files=files)
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

    def test_session(self):
        client = RequestsClient()
        response = client.get('http://testserver/session/')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {}
        assert response.json() == expected

        response = client.post('http://testserver/session/', json={'example': 'abc'})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {'example': 'abc'}
        assert response.json() == expected

        response = client.get('http://testserver/session/')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {'example': 'abc'}
        assert response.json() == expected

    def test_auth(self):
        # Confirm session is not authenticated
        client = RequestsClient()
        response = client.get('http://testserver/auth/')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'username': None
        }
        assert response.json() == expected
        assert 'csrftoken' in response.cookies
        csrftoken = response.cookies['csrftoken']

        user = User.objects.create(username='tom')
        user.set_password('password')
        user.save()

        # Perform a login
        response = client.post('http://testserver/auth/', json={
            'username': 'tom',
            'password': 'password'
        }, headers={'X-CSRFToken': csrftoken})
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'username': 'tom'
        }
        assert response.json() == expected

        # Confirm session is authenticated
        response = client.get('http://testserver/auth/')
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/json'
        expected = {
            'username': 'tom'
        }
        assert response.json() == expected
