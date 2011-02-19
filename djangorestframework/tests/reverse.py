from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse
from django.test import TestCase

from djangorestframework.resource import Resource

try:
    import json
except ImportError:
    import simplejson as json


class MockResource(Resource):
    """Mock resource which simply returns a URL, so that we can ensure that reversed URLs are fully qualified"""
    anon_allowed_methods = ('GET',)

    def get(self, request, auth):
        return reverse('another')

urlpatterns = patterns('',
    url(r'^$', MockResource.as_view()),
    url(r'^another$', MockResource.as_view(), name='another'),
)


class ReverseTests(TestCase):
    """Tests for """
    urls = 'djangorestframework.tests.reverse'

    def test_reversed_urls_are_fully_qualified(self):
        response = self.client.get('/')
        self.assertEqual(json.loads(response.content), 'http://testserver/another')
