from __future__ import unicode_literals

from django.conf.urls import url
from django.test import override_settings

from rest_framework.response import Response
from rest_framework.test import APITestCase
from rest_framework.views import APIView


class Root(APIView):
    def get(self, request):
        return Response({'hello': 'world'})


urlpatterns = [
    url(r'^$', Root.as_view()),
]


@override_settings(ROOT_URLCONF='tests.test_requests_client')
class RequestsClientTests(APITestCase):
    def test_get_root(self):
        print self.requests.get('http://example.com')
