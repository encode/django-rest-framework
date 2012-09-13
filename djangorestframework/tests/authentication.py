from django.conf.urls.defaults import patterns
from django.contrib.auth.models import User
from django.test import Client, TestCase

from django.utils import simplejson as json
from django.http import HttpResponse

from djangorestframework.views import APIView
from djangorestframework import permissions

from djangorestframework.authtoken.models import Token
from djangorestframework.authentication import TokenAuthentication

import base64


class MockView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def put(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

MockView.authentication_classes += (TokenAuthentication,)

urlpatterns = patterns('',
    (r'^$', MockView.as_view()),
)


class BasicAuthTests(TestCase):
    """Basic authentication"""
    urls = 'djangorestframework.tests.authentication'

    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

    def test_post_form_passing_basic_auth(self):
        """Ensure POSTing json over basic auth with correct credentials passes and does not require CSRF"""
        auth = 'Basic %s' % base64.encodestring('%s:%s' % (self.username, self.password)).strip()
        response = self.csrf_client.post('/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    def test_post_json_passing_basic_auth(self):
        """Ensure POSTing form over basic auth with correct credentials passes and does not require CSRF"""
        auth = 'Basic %s' % base64.encodestring('%s:%s' % (self.username, self.password)).strip()
        response = self.csrf_client.post('/', json.dumps({'example': 'example'}), 'application/json', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    def test_post_form_failing_basic_auth(self):
        """Ensure POSTing form over basic auth without correct credentials fails"""
        response = self.csrf_client.post('/', {'example': 'example'})
        self.assertEqual(response.status_code, 403)

    def test_post_json_failing_basic_auth(self):
        """Ensure POSTing json over basic auth without correct credentials fails"""
        response = self.csrf_client.post('/', json.dumps({'example': 'example'}), 'application/json')
        self.assertEqual(response.status_code, 403)


class SessionAuthTests(TestCase):
    """User session authentication"""
    urls = 'djangorestframework.tests.authentication'

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
        response = self.csrf_client.post('/', {'example': 'example'})
        self.assertEqual(response.status_code, 403)

    def test_post_form_session_auth_passing(self):
        """
        Ensure POSTing form over session authentication with logged in user and CSRF token passes.
        """
        self.non_csrf_client.login(username=self.username, password=self.password)
        response = self.non_csrf_client.post('/', {'example': 'example'})
        self.assertEqual(response.status_code, 200)

    def test_put_form_session_auth_passing(self):
        """
        Ensure PUTting form over session authentication with logged in user and CSRF token passes.
        """
        self.non_csrf_client.login(username=self.username, password=self.password)
        response = self.non_csrf_client.put('/', {'example': 'example'})
        self.assertEqual(response.status_code, 200)

    def test_post_form_session_auth_failing(self):
        """
        Ensure POSTing form over session authentication without logged in user fails.
        """
        response = self.csrf_client.post('/', {'example': 'example'})
        self.assertEqual(response.status_code, 403)


class TokenAuthTests(TestCase):
    """Token authentication"""
    urls = 'djangorestframework.tests.authentication'

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
        response = self.csrf_client.post('/', {'example': 'example'}, HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    def test_post_json_passing_token_auth(self):
        """Ensure POSTing form over token auth with correct credentials passes and does not require CSRF"""
        auth = "Token " + self.key
        response = self.csrf_client.post('/', json.dumps({'example': 'example'}), 'application/json', HTTP_AUTHORIZATION=auth)
        self.assertEqual(response.status_code, 200)

    def test_post_form_failing_token_auth(self):
        """Ensure POSTing form over token auth without correct credentials fails"""
        response = self.csrf_client.post('/', {'example': 'example'})
        self.assertEqual(response.status_code, 403)

    def test_post_json_failing_token_auth(self):
        """Ensure POSTing json over token auth without correct credentials fails"""
        response = self.csrf_client.post('/', json.dumps({'example': 'example'}), 'application/json')
        self.assertEqual(response.status_code, 403)

    def test_token_has_auto_assigned_key_if_none_provided(self):
        """Ensure creating a token with no key will auto-assign a key"""
        token = Token.objects.create(user=self.user)
        self.assertTrue(bool(token.key))
