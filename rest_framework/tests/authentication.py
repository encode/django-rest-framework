from __future__ import unicode_literals
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client, TestCase
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import (
    BaseAuthentication,
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
    OAuth2Authentication
)
from rest_framework.compat import patterns, url, include
from rest_framework.compat import oauth2
from rest_framework.compat import oauth2_provider
from rest_framework.tests.utils import RequestFactory
from rest_framework.views import APIView
import json
import base64
import datetime
import unittest


factory = RequestFactory()


class MockView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def post(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def put(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})


urlpatterns = patterns('',
    (r'^session/$', MockView.as_view(authentication_classes=[SessionAuthentication])),
    (r'^basic/$', MockView.as_view(authentication_classes=[BasicAuthentication])),
    (r'^token/$', MockView.as_view(authentication_classes=[TokenAuthentication])),
    (r'^auth-token/$', 'rest_framework.authtoken.views.obtain_auth_token'),
    url(r'^oauth2/', include('provider.oauth2.urls', namespace = 'oauth2')),
    url(r'^oauth2-test/$', MockView.as_view(authentication_classes=[OAuth2Authentication])),
)


class BasicAuthTests(TestCase):
    """Basic authentication"""
    urls = 'rest_framework.tests.authentication'

    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

    def test_post_form_passing_basic_auth(self):
        """Ensure POSTing json over basic auth with correct credentials passes and does not require CSRF"""
        credentials = ('%s:%s' % (self.username, self.password))
        base64_credentials = base64.b64encode(credentials.encode(HTTP_HEADER_ENCODING)).decode(HTTP_HEADER_ENCODING)
        auth = 'Basic %s' % base64_credentials
        response = self.csrf_client.post('/basic/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_json_passing_basic_auth(self):
        """Ensure POSTing form over basic auth with correct credentials passes and does not require CSRF"""
        credentials = ('%s:%s' % (self.username, self.password))
        base64_credentials = base64.b64encode(credentials.encode(HTTP_HEADER_ENCODING)).decode(HTTP_HEADER_ENCODING)
        auth = 'Basic %s' % base64_credentials
        response = self.csrf_client.post('/basic/', json.dumps({'example': 'example'}), 'application/json', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_form_failing_basic_auth(self):
        """Ensure POSTing form over basic auth without correct credentials fails"""
        response = self.csrf_client.post('/basic/', {'example': 'example'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_json_failing_basic_auth(self):
        """Ensure POSTing json over basic auth without correct credentials fails"""
        response = self.csrf_client.post('/basic/', json.dumps({'example': 'example'}), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response['WWW-Authenticate'], 'Basic realm="api"')


class SessionAuthTests(TestCase):
    """User session authentication"""
    urls = 'rest_framework.tests.authentication'

    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.non_csrf_client = Client(enforce_csrf_checks=False)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

    def tearDown(self):
        self.csrf_client.logout()

    def test_post_form_session_auth_failing_csrf(self):
        """
        Ensure POSTing form over session authentication without CSRF token fails.
        """
        self.csrf_client.login(username=self.username, password=self.password)
        response = self.csrf_client.post('/session/', {'example': 'example'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_post_form_session_auth_passing(self):
        """
        Ensure POSTing form over session authentication with logged in user and CSRF token passes.
        """
        self.non_csrf_client.login(username=self.username, password=self.password)
        response = self.non_csrf_client.post('/session/', {'example': 'example'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_put_form_session_auth_passing(self):
        """
        Ensure PUTting form over session authentication with logged in user and CSRF token passes.
        """
        self.non_csrf_client.login(username=self.username, password=self.password)
        response = self.non_csrf_client.put('/session/', {'example': 'example'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_form_session_auth_failing(self):
        """
        Ensure POSTing form over session authentication without logged in user fails.
        """
        response = self.csrf_client.post('/session/', {'example': 'example'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TokenAuthTests(TestCase):
    """Token authentication"""
    urls = 'rest_framework.tests.authentication'

    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

        self.key = 'abcd1234'
        self.token = Token.objects.create(key=self.key, user=self.user)

    def test_post_form_passing_token_auth(self):
        """Ensure POSTing json over token auth with correct credentials passes and does not require CSRF"""
        auth = "Token " + self.key
        response = self.csrf_client.post('/token/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_json_passing_token_auth(self):
        """Ensure POSTing form over token auth with correct credentials passes and does not require CSRF"""
        auth = "Token " + self.key
        response = self.csrf_client.post('/token/', json.dumps({'example': 'example'}), 'application/json', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_form_failing_token_auth(self):
        """Ensure POSTing form over token auth without correct credentials fails"""
        response = self.csrf_client.post('/token/', {'example': 'example'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_post_json_failing_token_auth(self):
        """Ensure POSTing json over token auth without correct credentials fails"""
        response = self.csrf_client.post('/token/', json.dumps({'example': 'example'}), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_has_auto_assigned_key_if_none_provided(self):
        """Ensure creating a token with no key will auto-assign a key"""
        self.token.delete()
        token = Token.objects.create(user=self.user)
        self.assertTrue(bool(token.key))

    def test_token_login_json(self):
        """Ensure token login view using JSON POST works."""
        client = Client(enforce_csrf_checks=True)
        response = client.post('/auth-token/',
                               json.dumps({'username': self.username, 'password': self.password}), 'application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode('ascii'))['token'], self.key)

    def test_token_login_json_bad_creds(self):
        """Ensure token login view using JSON POST fails if bad credentials are used."""
        client = Client(enforce_csrf_checks=True)
        response = client.post('/auth-token/',
                               json.dumps({'username': self.username, 'password': "badpass"}), 'application/json')
        self.assertEqual(response.status_code, 400)

    def test_token_login_json_missing_fields(self):
        """Ensure token login view using JSON POST fails if missing fields."""
        client = Client(enforce_csrf_checks=True)
        response = client.post('/auth-token/',
                               json.dumps({'username': self.username}), 'application/json')
        self.assertEqual(response.status_code, 400)

    def test_token_login_form(self):
        """Ensure token login view using form POST works."""
        client = Client(enforce_csrf_checks=True)
        response = client.post('/auth-token/',
                               {'username': self.username, 'password': self.password})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(response.content.decode('ascii'))['token'], self.key)


class IncorrectCredentialsTests(TestCase):
    def test_incorrect_credentials(self):
        """
        If a request contains bad authentication credentials, then
        authentication should run and error, even if no permissions
        are set on the view.
        """
        class IncorrectCredentialsAuth(BaseAuthentication):
            def authenticate(self, request):
                raise exceptions.AuthenticationFailed('Bad credentials')

        request = factory.get('/')
        view = MockView.as_view(
            authentication_classes=(IncorrectCredentialsAuth,),
            permission_classes=()
        )
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {'detail': 'Bad credentials'})


class OAuth2Tests(TestCase):
    """OAuth 2.0 authentication"""
    urls = 'rest_framework.tests.authentication'

    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

        self.CLIENT_ID = 'client_key'
        self.CLIENT_SECRET = 'client_secret'
        self.ACCESS_TOKEN = "access_token"
        self.REFRESH_TOKEN = "refresh_token"

        self.oauth2_client = oauth2.models.Client.objects.create(
                client_id=self.CLIENT_ID, 
                client_secret=self.CLIENT_SECRET,
                redirect_uri='',
                client_type=0,
                name='example', 
                user=None,
            )

        self.access_token = oauth2.models.AccessToken.objects.create(
                token=self.ACCESS_TOKEN,
                client=self.oauth2_client,
                user=self.user,
            )
        self.refresh_token = oauth2.models.RefreshToken.objects.create(
                user=self.user,
                access_token=self.access_token,
                client=self.oauth2_client
            )

    def _create_authorization_header(self, token=None):
        return "Bearer {0}".format(token or self.access_token.token)

    def _client_credentials_params(self):
        return {'client_id': self.CLIENT_ID, 'client_secret': self.CLIENT_SECRET}

    @unittest.skipUnless(oauth2, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_client_data_failing_auth(self):
        """Ensure GETing form over OAuth with incorrect client credentials fails"""
        auth = self._create_authorization_header()
        params = self._client_credentials_params()
        params['client_id'] += 'a'
        response = self.csrf_client.get('/oauth2-test/', params, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(oauth2, 'django-oauth2-provider not installed')
    def test_get_form_passing_auth(self):
        """Ensure GETing form over OAuth with correct client credentials succeed"""
        auth = self._create_authorization_header()
        params = self._client_credentials_params()
        response = self.csrf_client.get('/oauth2-test/', params, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth2, 'django-oauth2-provider not installed')
    def test_post_form_passing_auth(self):
        """Ensure POSTing form over OAuth with correct credentials passes and does not require CSRF"""
        auth = self._create_authorization_header()
        params = self._client_credentials_params()
        response = self.csrf_client.post('/oauth2-test/', params, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth2, 'django-oauth2-provider not installed')
    def test_post_form_token_removed_failing_auth(self):
        """Ensure POSTing when there is no OAuth access token in db fails"""
        self.access_token.delete()
        auth = self._create_authorization_header()
        params = self._client_credentials_params()
        response = self.csrf_client.post('/oauth2-test/', params, HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth2, 'django-oauth2-provider not installed')
    def test_post_form_with_refresh_token_failing_auth(self):
        """Ensure POSTing with refresh token instead of access token fails"""
        auth = self._create_authorization_header(token=self.refresh_token.token)
        params = self._client_credentials_params()
        response = self.csrf_client.post('/oauth2-test/', params, HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth2, 'django-oauth2-provider not installed')
    def test_post_form_with_expired_access_token_failing_auth(self):
        """Ensure POSTing with expired access token fails with an 'Invalid token' error"""
        self.access_token.expires = datetime.datetime.now() - datetime.timedelta(seconds=10)  # 10 seconds late
        self.access_token.save()
        auth = self._create_authorization_header()
        params = self._client_credentials_params()
        response = self.csrf_client.post('/oauth2-test/', params, HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertIn('Invalid token', response.content)
