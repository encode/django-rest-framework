# -- coding: utf-8 --

from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.compat import patterns, url
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.test import APIClient


@api_view(['GET'])
def mirror(request):
    return Response({
        'auth': request.META.get('HTTP_AUTHORIZATION', b'')
    })


urlpatterns = patterns('',
    url(r'^view/$', mirror),
)


class CheckTestClient(TestCase):
    urls = 'rest_framework.tests.test_testing'

    def setUp(self):
        self.client = APIClient()

    def test_credentials(self):
        self.client.credentials(HTTP_AUTHORIZATION='example')
        response = self.client.get('/view/')
        self.assertEqual(response.data['auth'], 'example')
