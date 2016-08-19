from __future__ import unicode_literals

import unittest

from django.conf.urls import url
from django.test import override_settings

from rest_framework.compat import coreapi
from rest_framework.response import Response
from rest_framework.test import APITestCase, get_api_client
from rest_framework.views import APIView


class Root(APIView):
    def get(self, request):
        return Response({
            'hello': 'world',
        })


urlpatterns = [
    url(r'^$', Root.as_view()),
]


@unittest.skipUnless(coreapi, 'coreapi not installed')
@override_settings(ROOT_URLCONF='tests.test_api_client')
class APIClientTests(APITestCase):
    def test_api_client(self):
        client = get_api_client()
        schema = client.get('/')
        data = client.action(schema, ['echo'])
        assert data == {'hello': 'world'}
