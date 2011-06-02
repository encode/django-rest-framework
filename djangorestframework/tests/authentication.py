from django.conf.urls.defaults import patterns
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.test import Client, TestCase

from django.utils import simplejson as json

from djangorestframework.compat import RequestFactory
from djangorestframework.views import View
from djangorestframework import permissions

import base64


class MockView(View):
    permissions = ( permissions.IsAuthenticated, )
    def post(self, request):
        return {'a':1, 'b':2, 'c':3}

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
        """Ensure POSTing form over session authentication without CSRF token fails."""
        self.csrf_client.login(username=self.username, password=self.password)
        response = self.csrf_client.post('/', {'example': 'example'})
        self.assertEqual(response.status_code, 403)

    def test_post_form_session_auth_passing(self):
        """Ensure POSTing form over session authentication with logged in user and CSRF token passes."""
        self.non_csrf_client.login(username=self.username, password=self.password)
        response = self.non_csrf_client.post('/', {'example': 'example'})
        self.assertEqual(response.status_code, 200)

    def test_post_form_session_auth_failing(self):
        """Ensure POSTing form over session authentication without logged in user fails."""
        response = self.csrf_client.post('/', {'example': 'example'})
        self.assertEqual(response.status_code, 403)

