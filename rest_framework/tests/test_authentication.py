from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import Client, TestCase
from django.utils import unittest
from rest_framework import HTTP_HEADER_ENCODING
from rest_framework import exceptions
from rest_framework import permissions
from rest_framework import renderers
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import (
    BaseAuthentication,
    TokenAuthentication,
    BasicAuthentication,
    SessionAuthentication,
    OAuthAuthentication,
    OAuth2Authentication
)
from rest_framework.authtoken.models import Token
from rest_framework.compat import patterns, url, include
from rest_framework.compat import oauth2_provider, oauth2_provider_models, oauth2_provider_scope
from rest_framework.compat import oauth, oauth_provider
from rest_framework.tests.utils import RequestFactory
from rest_framework.views import APIView
import json
import base64
import time
import datetime

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
    (r'^oauth/$', MockView.as_view(authentication_classes=[OAuthAuthentication])),
    (r'^oauth-with-scope/$', MockView.as_view(authentication_classes=[OAuthAuthentication],
        permission_classes=[permissions.TokenHasReadWriteScope]))
)

if oauth2_provider is not None:
    urlpatterns += patterns('',
        url(r'^oauth2/', include('provider.oauth2.urls', namespace='oauth2')),
        url(r'^oauth2-test/$', MockView.as_view(authentication_classes=[OAuth2Authentication])),
        url(r'^oauth2-with-scope-test/$', MockView.as_view(authentication_classes=[OAuth2Authentication],
            permission_classes=[permissions.TokenHasReadWriteScope])),
    )


class BasicAuthTests(TestCase):
    """Basic authentication"""
    urls = 'rest_framework.tests.test_authentication'

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
    urls = 'rest_framework.tests.test_authentication'

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
    urls = 'rest_framework.tests.test_authentication'

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
        auth = 'Token ' + self.key
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


class OAuthTests(TestCase):
    """OAuth 1.0a authentication"""
    urls = 'rest_framework.tests.test_authentication'

    def setUp(self):
        # these imports are here because oauth is optional and hiding them in try..except block or compat
        # could obscure problems if something breaks
        from oauth_provider.models import Consumer, Resource
        from oauth_provider.models import Token as OAuthToken
        from oauth_provider import consts

        self.consts = consts

        self.csrf_client = Client(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

        self.CONSUMER_KEY = 'consumer_key'
        self.CONSUMER_SECRET = 'consumer_secret'
        self.TOKEN_KEY = "token_key"
        self.TOKEN_SECRET = "token_secret"

        self.consumer = Consumer.objects.create(key=self.CONSUMER_KEY, secret=self.CONSUMER_SECRET,
            name='example', user=self.user, status=self.consts.ACCEPTED)

        self.resource = Resource.objects.create(name="resource name", url="api/")
        self.token = OAuthToken.objects.create(user=self.user, consumer=self.consumer, resource=self.resource,
            token_type=OAuthToken.ACCESS, key=self.TOKEN_KEY, secret=self.TOKEN_SECRET, is_approved=True
        )

    def _create_authorization_header(self):
        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'oauth_token': self.token.key,
            'oauth_consumer_key': self.consumer.key
        }

        req = oauth.Request(method="GET", url="http://example.com", parameters=params)

        signature_method = oauth.SignatureMethod_PLAINTEXT()
        req.sign_request(signature_method, self.consumer, self.token)

        return req.to_header()["Authorization"]

    def _create_authorization_url_parameters(self):
        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'oauth_token': self.token.key,
            'oauth_consumer_key': self.consumer.key
        }

        req = oauth.Request(method="GET", url="http://example.com", parameters=params)

        signature_method = oauth.SignatureMethod_PLAINTEXT()
        req.sign_request(signature_method, self.consumer, self.token)
        return dict(req)

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_form_passing_oauth(self):
        """Ensure POSTing form over OAuth with correct credentials passes and does not require CSRF"""
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_form_repeated_nonce_failing_oauth(self):
        """Ensure POSTing form over OAuth with repeated auth (same nonces and timestamp) credentials fails"""
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

        # simulate reply attack auth header containes already used (nonce, timestamp) pair
        response = self.csrf_client.post('/oauth/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_form_token_removed_failing_oauth(self):
        """Ensure POSTing when there is no OAuth access token in db fails"""
        self.token.delete()
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_form_consumer_status_not_accepted_failing_oauth(self):
        """Ensure POSTing when consumer status is anything other than ACCEPTED fails"""
        for consumer_status in (self.consts.CANCELED, self.consts.PENDING, self.consts.REJECTED):
            self.consumer.status = consumer_status
            self.consumer.save()

            auth = self._create_authorization_header()
            response = self.csrf_client.post('/oauth/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
            self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_form_with_request_token_failing_oauth(self):
        """Ensure POSTing with unauthorized request token instead of access token fails"""
        self.token.token_type = self.token.REQUEST
        self.token.save()

        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_form_with_urlencoded_parameters(self):
        """Ensure POSTing with x-www-form-urlencoded auth parameters passes"""
        params = self._create_authorization_url_parameters()
        response = self.csrf_client.post('/oauth/', params)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_get_form_with_url_parameters(self):
        """Ensure GETing with auth in url parameters passes"""
        params = self._create_authorization_url_parameters()
        response = self.csrf_client.get('/oauth/', params)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_hmac_sha1_signature_passes(self):
        """Ensure POSTing using HMAC_SHA1 signature method passes"""
        params = {
            'oauth_version': "1.0",
            'oauth_nonce': oauth.generate_nonce(),
            'oauth_timestamp': int(time.time()),
            'oauth_token': self.token.key,
            'oauth_consumer_key': self.consumer.key
        }

        req = oauth.Request(method="POST", url="http://testserver/oauth/", parameters=params)

        signature_method = oauth.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, self.consumer, self.token)
        auth = req.to_header()["Authorization"]

        response = self.csrf_client.post('/oauth/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_get_form_with_readonly_resource_passing_auth(self):
        """Ensure POSTing with a readonly resource instead of a write scope fails"""
        read_only_access_token = self.token
        read_only_access_token.resource.is_readonly = True
        read_only_access_token.resource.save()
        params = self._create_authorization_url_parameters()
        response = self.csrf_client.get('/oauth-with-scope/', params)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_form_with_readonly_resource_failing_auth(self):
        """Ensure POSTing with a readonly resource instead of a write scope fails"""
        read_only_access_token = self.token
        read_only_access_token.resource.is_readonly = True
        read_only_access_token.resource.save()
        params = self._create_authorization_url_parameters()
        response = self.csrf_client.post('/oauth-with-scope/', params)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth_provider, 'django-oauth-plus not installed')
    @unittest.skipUnless(oauth, 'oauth2 not installed')
    def test_post_form_with_write_resource_passing_auth(self):
        """Ensure POSTing with a write resource succeed"""
        read_write_access_token = self.token
        read_write_access_token.resource.is_readonly = False
        read_write_access_token.resource.save()
        params = self._create_authorization_url_parameters()
        response = self.csrf_client.post('/oauth-with-scope/', params)
        self.assertEqual(response.status_code, 200)


class OAuth2Tests(TestCase):
    """OAuth 2.0 authentication"""
    urls = 'rest_framework.tests.test_authentication'

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

        self.oauth2_client = oauth2_provider_models.Client.objects.create(
                client_id=self.CLIENT_ID,
                client_secret=self.CLIENT_SECRET,
                redirect_uri='',
                client_type=0,
                name='example',
                user=None,
            )

        self.access_token = oauth2_provider_models.AccessToken.objects.create(
                token=self.ACCESS_TOKEN,
                client=self.oauth2_client,
                user=self.user,
            )
        self.refresh_token = oauth2_provider_models.RefreshToken.objects.create(
                user=self.user,
                access_token=self.access_token,
                client=self.oauth2_client
            )

    def _create_authorization_header(self, token=None):
        return "Bearer {0}".format(token or self.access_token.token)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_authorization_header_token_type_failing(self):
        """Ensure that a wrong token type lead to the correct HTTP error status code"""
        auth = "Wrong token-type-obsviously"
        response = self.csrf_client.get('/oauth2-test/', {}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_authorization_header_token_format_failing(self):
        """Ensure that a wrong token format lead to the correct HTTP error status code"""
        auth = "Bearer wrong token format"
        response = self.csrf_client.get('/oauth2-test/', {}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_with_wrong_authorization_header_token_failing(self):
        """Ensure that a wrong token lead to the correct HTTP error status code"""
        auth = "Bearer wrong-token"
        response = self.csrf_client.get('/oauth2-test/', {}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_get_form_passing_auth(self):
        """Ensure GETing form over OAuth with correct client credentials succeed"""
        auth = self._create_authorization_header()
        response = self.csrf_client.get('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_passing_auth(self):
        """Ensure POSTing form over OAuth with correct credentials passes and does not require CSRF"""
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_token_removed_failing_auth(self):
        """Ensure POSTing when there is no OAuth access token in db fails"""
        self.access_token.delete()
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_refresh_token_failing_auth(self):
        """Ensure POSTing with refresh token instead of access token fails"""
        auth = self._create_authorization_header(token=self.refresh_token.token)
        response = self.csrf_client.post('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_expired_access_token_failing_auth(self):
        """Ensure POSTing with expired access token fails with an 'Invalid token' error"""
        self.access_token.expires = datetime.datetime.now() - datetime.timedelta(seconds=10)  # 10 seconds late
        self.access_token.save()
        auth = self._create_authorization_header()
        response = self.csrf_client.post('/oauth2-test/', HTTP_AUTHORIZATION=auth)
        self.assertIn(response.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))
        self.assertIn('Invalid token', response.content)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_invalid_scope_failing_auth(self):
        """Ensure POSTing with a readonly scope instead of a write scope fails"""
        read_only_access_token = self.access_token
        read_only_access_token.scope = oauth2_provider_scope.SCOPE_NAME_DICT['read']
        read_only_access_token.save()
        auth = self._create_authorization_header(token=read_only_access_token.token)
        response = self.csrf_client.get('/oauth2-with-scope-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)
        response = self.csrf_client.post('/oauth2-with-scope-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @unittest.skipUnless(oauth2_provider, 'django-oauth2-provider not installed')
    def test_post_form_with_valid_scope_passing_auth(self):
        """Ensure POSTing with a write scope succeed"""
        read_write_access_token = self.access_token
        read_write_access_token.scope = oauth2_provider_scope.SCOPE_NAME_DICT['write']
        read_write_access_token.save()
        auth = self._create_authorization_header(token=read_write_access_token.token)
        response = self.csrf_client.post('/oauth2-with-scope-test/', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)


class FailingAuthAccessedInRenderer(TestCase):
    def setUp(self):
        class AuthAccessingRenderer(renderers.BaseRenderer):
            media_type = 'text/plain'
            format = 'txt'

            def render(self, data, media_type=None, renderer_context=None):
                request = renderer_context['request']
                if request.user.is_authenticated():
                    return b'authenticated'
                return b'not authenticated'

        class FailingAuth(BaseAuthentication):
            def authenticate(self, request):
                raise exceptions.AuthenticationFailed('authentication failed')

        class ExampleView(APIView):
            authentication_classes = (FailingAuth,)
            renderer_classes = (AuthAccessingRenderer,)

            def get(self, request):
                return Response({'foo': 'bar'})

        self.view = ExampleView.as_view()

    def test_failing_auth_accessed_in_renderer(self):
        """
        When authentication fails the renderer should still be able to access
        `request.user` without raising an exception. Particularly relevant
        to HTML responses that might reasonably access `request.user`.
        """
        request = factory.get('/')
        response = self.view(request)
        content = response.render().content
        self.assertEqual(content, b'not authenticated')
