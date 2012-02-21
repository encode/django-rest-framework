from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from django.utils import simplejson as json

from djangorestframework.utils import reverse
from djangorestframework.views import View
from djangorestframework.response import Response


class MockView(View):
    """Mock resource which simply returns a URL, so that we can ensure that reversed URLs are fully qualified"""
    permissions = ()

    def get(self, request):
        return Response(reverse('another', request))

urlpatterns = patterns('',
    url(r'^$', MockView.as_view()),
    url(r'^another$', MockView.as_view(), name='another'),
)


class ReverseTests(TestCase):
    """Tests for """
    urls = 'djangorestframework.tests.reverse'

    def test_reversed_urls_are_fully_qualified(self):
        response = self.client.get('/')
        self.assertEqual(json.loads(response.content), 'http://testserver/another')
