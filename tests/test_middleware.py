import base64
import unittest

import django
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.test import override_settings
from django.urls import path
from django.views import View

from rest_framework import HTTP_HEADER_ENCODING, status
from rest_framework.authentication import (
    BasicAuthentication, TokenAuthentication
)
from rest_framework.authtoken.models import Token
from rest_framework.request import is_form_media_type
from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView


class PostAPIView(APIView):
    def post(self, request):
        return Response(data=request.data, status=200)


class GetAPIView(APIView):
    def get(self, request):
        return Response(data={"status": "ok"}, status=200)


class GetView(View):
    def get(self, request):
        return HttpResponse("OK", status=200)


urlpatterns = [
    path('api/auth', APIView.as_view(authentication_classes=(TokenAuthentication,))),
    path('api/post', PostAPIView.as_view()),
    path('api/get', GetAPIView.as_view()),
    path('api/basic', GetAPIView.as_view(authentication_classes=(BasicAuthentication,))),
    path('api/token', GetAPIView.as_view(authentication_classes=(TokenAuthentication,))),
    path('get', GetView.as_view()),
]


class RequestUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        assert hasattr(request, 'user'), '`user` is not set on request'
        assert request.user.is_authenticated, '`user` is not authenticated'

        return response


class RequestPOSTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        assert isinstance(request, HttpRequest)

        # Parse body with underlying Django request
        request.body

        # Process request with DRF view
        response = self.get_response(request)

        # Ensure request.POST is set as appropriate
        if is_form_media_type(request.content_type):
            assert request.POST == {'foo': ['bar']}
        else:
            assert request.POST == {}

        return response


@override_settings(ROOT_URLCONF='tests.test_middleware')
class TestMiddleware(APITestCase):

    @override_settings(MIDDLEWARE=('tests.test_middleware.RequestUserMiddleware',))
    def test_middleware_can_access_user_when_processing_response(self):
        user = User.objects.create_user('john', 'john@example.com', 'password')
        key = 'abcd1234'
        Token.objects.create(key=key, user=user)

        self.client.get('/api/auth', HTTP_AUTHORIZATION='Token %s' % key)

    @override_settings(MIDDLEWARE=('tests.test_middleware.RequestPOSTMiddleware',))
    def test_middleware_can_access_request_post_when_processing_response(self):
        response = self.client.post('/api/post', {'foo': 'bar'})
        assert response.status_code == 200

        response = self.client.post('/api/post', {'foo': 'bar'}, format='json')
        assert response.status_code == 200


@unittest.skipUnless(django.VERSION >= (5, 1), 'Only for Django 5.1+')
@override_settings(
    ROOT_URLCONF='tests.test_middleware',
    MIDDLEWARE=(
        # Needed for AuthenticationMiddleware
        'django.contrib.sessions.middleware.SessionMiddleware',
        # Needed for LoginRequiredMiddleware
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'rest_framework.middleware.LoginRequiredMiddleware',
    ),
    REST_FRAMEWORK={
        'DEFAULT_PERMISSION_CLASSES': [
            'rest_framework.permissions.IsAuthenticated',
        ],
    }
)
class TestLoginRequiredMiddleware(APITestCase):
    def test_unauthorized_when_user_is_anonymous_on_public_view(self):
        response = self.client.get('/api/get')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthorized_when_user_is_anonymous_on_basic_auth_view(self):
        response = self.client.get('/api/basic')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthorized_when_user_is_anonymous_on_token_auth_view(self):
        response = self.client.get('/api/token')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_allows_request_when_session_authenticated(self):
        user = User.objects.create_user('john', 'john@example.com', 'password')
        self.client.force_login(user)

        response = self.client.get('/api/get')
        assert response.status_code == status.HTTP_200_OK

    def test_allows_request_when_token_authenticated(self):
        user = User.objects.create_user('john', 'john@example.com', 'password')
        key = 'abcd1234'
        Token.objects.create(key=key, user=user)

        response = self.client.get('/api/token', headers={"Authorization": f'Token {key}'})
        assert response.status_code == status.HTTP_200_OK

    def test_allows_request_when_basic_authenticated(self):
        user = User.objects.create_user('john', 'john@example.com', 'password')
        credentials = ('%s:%s' % (user.username, user.password))
        base64_credentials = base64.b64encode(
            credentials.encode(HTTP_HEADER_ENCODING)
        ).decode(HTTP_HEADER_ENCODING)
        auth = f'Basic {base64_credentials}'
        response = self.client.get('/api/basic', headers={"Authorization": auth})
        assert response.status_code == status.HTTP_200_OK

    def test_works_as_base_middleware_for_django_view(self):
        response = self.client.get('/get')
        self.assertRedirects(response, '/accounts/login/?next=/get', fetch_redirect_response=False)
