# -- coding: utf-8 --

from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.compat import patterns, url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIClient


@api_view(['GET', 'POST'])
def mirror(request):
    return Response({
        'auth': request.META.get('HTTP_AUTHORIZATION', b''),
        'user': request.user.username
    })


urlpatterns = patterns('',
    url(r'^view/$', mirror),
)


class CheckTestClient(TestCase):
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

    def test_authenticate(self):
        """
        Setting `.authenticate()` forcibly authenticates each request.
        """
        user = User.objects.create_user('example', 'example@example.com')
        self.client.authenticate(user)
        response = self.client.get('/view/')
        self.assertEqual(response.data['user'], 'example')

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
