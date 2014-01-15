# -- coding: utf-8 --

from __future__ import unicode_literals
import tempfile
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.compat import patterns, url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate


BOUNDARY = 'BoUnDaRyStRiNg'
MULTIPART_CONTENT = 'multipart/form-data; boundary=%s' % BOUNDARY


@api_view(['GET', 'POST'])
def view(request):
    return Response({
        'auth': request.META.get('HTTP_AUTHORIZATION', b''),
        'user': request.user.username
    })


@api_view(['GET', 'POST'])
def session_view(request):
    active_session = request.session.get('active_session', False)
    request.session['active_session'] = True
    return Response({
        'active_session': active_session
    })


@api_view(['GET', 'POST'])
def echo(request):
    return Response({
        'data': request.DATA.dict(),
        'files': request.FILES.dict()
    })


urlpatterns = patterns('',
    url(r'^view/$', view),
    url(r'^session-view/$', session_view),
    url(r'^echo/$', echo),
)


class TestAPITestClient(TestCase):
    urls = 'rest_framework.tests.test_testing'

    def setUp(self):
        self.client = APIClient()

    def test_credentials(self):
        """
        Setting `.credentials()` adds the required headers to each request.
        """
        self.client.credentials(HTTP_AUTHORIZATION='example')
        for _ in range(0, 3):
            response = self.client.get('/view/')
            self.assertEqual(response.data['auth'], 'example')

    def test_force_authenticate(self):
        """
        Setting `.force_authenticate()` forcibly authenticates each request.
        """
        user = User.objects.create_user('example', 'example@example.com')
        self.client.force_authenticate(user)
        response = self.client.get('/view/')
        self.assertEqual(response.data['user'], 'example')

    def test_force_authenticate_with_sessions(self):
        """
        Setting `.force_authenticate()` forcibly authenticates each request.
        """
        user = User.objects.create_user('example', 'example@example.com')
        self.client.force_authenticate(user)

        # First request does not yet have an active session
        response = self.client.get('/session-view/')
        self.assertEqual(response.data['active_session'], False)

        # Subsequant requests have an active session
        response = self.client.get('/session-view/')
        self.assertEqual(response.data['active_session'], True)

        # Force authenticating as `None` should also logout the user session.
        self.client.force_authenticate(None)
        response = self.client.get('/session-view/')
        self.assertEqual(response.data['active_session'], False)

    def test_csrf_exempt_by_default(self):
        """
        By default, the test client is CSRF exempt.
        """
        User.objects.create_user('example', 'example@example.com', 'password')
        self.client.login(username='example', password='password')
        response = self.client.post('/view/')
        self.assertEqual(response.status_code, 200)

    def test_explicitly_enforce_csrf_checks(self):
        """
        The test client can enforce CSRF checks.
        """
        client = APIClient(enforce_csrf_checks=True)
        User.objects.create_user('example', 'example@example.com', 'password')
        client.login(username='example', password='password')
        response = client.post('/view/')
        expected = {'detail': 'CSRF Failed: CSRF cookie not set.'}
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, expected)

    def test_echo(self):
        """
        The echo test view returns the request data as-is.
        """
        example_data = {'foo': 'bar'}
        response = self.client.post('/echo/', example_data)
        self.assertEqual(response.data['data'], example_data)
        self.assertEqual(response.data['files'], {})

    def test_echo_multipart(self):
        """
        The test client sends data correctly with multipart content type.
        """
        example_data = {'foo': 'bar'}
        response = self.client.post('/echo/', example_data, content_type=MULTIPART_CONTENT)
        self.assertEqual(response.data['data'], example_data)
        self.assertEqual(response.data['files'], {})

    def test_fileupload(self):
        """
        The test client is capable of uploading a file.
        """
        with tempfile.NamedTemporaryFile(suffix='.txt') as example_file:
            example_file.write(b'This is a dummy file.')
            example_file.seek(0)
            response = self.client.post(
                '/echo/',
                {'file': example_file},
            )
        self.assertEqual(list(response.data['files'].keys()), [u'file'])


class TestAPIRequestFactory(TestCase):
    def test_csrf_exempt_by_default(self):
        """
        By default, the test client is CSRF exempt.
        """
        user = User.objects.create_user('example', 'example@example.com', 'password')
        factory = APIRequestFactory()
        request = factory.post('/view/')
        request.user = user
        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_explicitly_enforce_csrf_checks(self):
        """
        The test client can enforce CSRF checks.
        """
        user = User.objects.create_user('example', 'example@example.com', 'password')
        factory = APIRequestFactory(enforce_csrf_checks=True)
        request = factory.post('/view/')
        request.user = user
        response = view(request)
        expected = {'detail': 'CSRF Failed: CSRF cookie not set.'}
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data, expected)

    def test_invalid_format(self):
        """
        Attempting to use a format that is not configured will raise an
        assertion error.
        """
        factory = APIRequestFactory()
        self.assertRaises(AssertionError, factory.post,
            path='/view/', data={'example': 1}, format='xml'
        )

    def test_force_authenticate(self):
        """
        Setting `force_authenticate()` forcibly authenticates the request.
        """
        user = User.objects.create_user('example', 'example@example.com')
        factory = APIRequestFactory()
        request = factory.get('/view')
        force_authenticate(request, user=user)
        response = view(request)
        self.assertEqual(response.data['user'], 'example')
