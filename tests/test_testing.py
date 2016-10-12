# encoding: utf-8
from __future__ import unicode_literals

from io import BytesIO

from django.conf.urls import url
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.test import TestCase, override_settings

from rest_framework import fields, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import (
    APIClient, APIRequestFactory, force_authenticate
)


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


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
def redirect_view(request):
    return redirect('/view/')


class BasicSerializer(serializers.Serializer):
    flag = fields.BooleanField(default=lambda: True)


@api_view(['POST'])
def post_view(request):
    serializer = BasicSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data)


urlpatterns = [
    url(r'^view/$', view),
    url(r'^session-view/$', session_view),
    url(r'^redirect-view/$', redirect_view),
    url(r'^post-view/$', post_view)
]


@override_settings(ROOT_URLCONF='tests.test_testing')
class TestAPITestClient(TestCase):
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

        # Subsequent requests have an active session
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

    def test_can_logout(self):
        """
        `logout()` resets stored credentials
        """
        self.client.credentials(HTTP_AUTHORIZATION='example')
        response = self.client.get('/view/')
        self.assertEqual(response.data['auth'], 'example')
        self.client.logout()
        response = self.client.get('/view/')
        self.assertEqual(response.data['auth'], b'')

    def test_logout_resets_force_authenticate(self):
        """
        `logout()` resets any `force_authenticate`
        """
        user = User.objects.create_user('example', 'example@example.com', 'password')
        self.client.force_authenticate(user)
        response = self.client.get('/view/')
        self.assertEqual(response.data['user'], 'example')
        self.client.logout()
        response = self.client.get('/view/')
        self.assertEqual(response.data['user'], '')

    def test_follow_redirect(self):
        """
        Follow redirect by setting follow argument.
        """
        response = self.client.get('/redirect-view/')
        self.assertEqual(response.status_code, 302)
        response = self.client.get('/redirect-view/', follow=True)
        self.assertIsNotNone(response.redirect_chain)
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/redirect-view/')
        self.assertEqual(response.status_code, 302)
        response = self.client.post('/redirect-view/', follow=True)
        self.assertIsNotNone(response.redirect_chain)
        self.assertEqual(response.status_code, 200)

        response = self.client.put('/redirect-view/')
        self.assertEqual(response.status_code, 302)
        response = self.client.put('/redirect-view/', follow=True)
        self.assertIsNotNone(response.redirect_chain)
        self.assertEqual(response.status_code, 200)

        response = self.client.patch('/redirect-view/')
        self.assertEqual(response.status_code, 302)
        response = self.client.patch('/redirect-view/', follow=True)
        self.assertIsNotNone(response.redirect_chain)
        self.assertEqual(response.status_code, 200)

        response = self.client.delete('/redirect-view/')
        self.assertEqual(response.status_code, 302)
        response = self.client.delete('/redirect-view/', follow=True)
        self.assertIsNotNone(response.redirect_chain)
        self.assertEqual(response.status_code, 200)

        response = self.client.options('/redirect-view/')
        self.assertEqual(response.status_code, 302)
        response = self.client.options('/redirect-view/', follow=True)
        self.assertIsNotNone(response.redirect_chain)
        self.assertEqual(response.status_code, 200)

    def test_invalid_multipart_data(self):
        """
        MultiPart encoding cannot support nested data, so raise a helpful
        error if the user attempts to do so.
        """
        self.assertRaises(
            AssertionError, self.client.post,
            path='/view/', data={'valid': 123, 'invalid': {'a': 123}}
        )

    def test_empty_post_uses_default_boolean_value(self):
        response = self.client.post(
            '/post-view/',
            data=None,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.data, {"flag": True})


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
        self.assertRaises(
            AssertionError, factory.post,
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

    def test_upload_file(self):
        # This is a 1x1 black png
        simple_png = BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc````\x00\x00\x00\x05\x00\x01\xa5\xf6E@\x00\x00\x00\x00IEND\xaeB`\x82')
        simple_png.name = 'test.png'
        factory = APIRequestFactory()
        factory.post('/', data={'image': simple_png})

    def test_request_factory_url_arguments(self):
        """
        This is a non regression test against #1461
        """
        factory = APIRequestFactory()
        request = factory.get('/view/?demo=test')
        self.assertEqual(dict(request.GET), {'demo': ['test']})
        request = factory.get('/view/', {'demo': 'test'})
        self.assertEqual(dict(request.GET), {'demo': ['test']})

    def test_request_factory_url_arguments_with_unicode(self):
        factory = APIRequestFactory()
        request = factory.get('/view/?demo=testé')
        self.assertEqual(dict(request.GET), {'demo': ['testé']})
        request = factory.get('/view/', {'demo': 'testé'})
        self.assertEqual(dict(request.GET), {'demo': ['testé']})
