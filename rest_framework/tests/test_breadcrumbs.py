from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.compat import patterns, url
from rest_framework.utils.breadcrumbs import get_breadcrumbs
from rest_framework.views import APIView


class Root(APIView):
    pass


class ResourceRoot(APIView):
    pass


class ResourceInstance(APIView):
    pass


class NestedResourceRoot(APIView):
    pass


class NestedResourceInstance(APIView):
    pass

urlpatterns = patterns('',
    url(r'^$', Root.as_view()),
    url(r'^resource/$', ResourceRoot.as_view()),
    url(r'^resource/(?P<key>[0-9]+)$', ResourceInstance.as_view()),
    url(r'^resource/(?P<key>[0-9]+)/$', NestedResourceRoot.as_view()),
    url(r'^resource/(?P<key>[0-9]+)/(?P<other>[A-Za-z]+)$', NestedResourceInstance.as_view()),
)


class BreadcrumbTests(TestCase):
    """Tests the breadcrumb functionality used by the HTML renderer."""

    urls = 'rest_framework.tests.test_breadcrumbs'

    def test_root_breadcrumbs(self):
        url = '/'
        self.assertEqual(get_breadcrumbs(url), [('Root', '/')])

    def test_resource_root_breadcrumbs(self):
        url = '/resource/'
        self.assertEqual(get_breadcrumbs(url), [('Root', '/'),
                                            ('Resource Root', '/resource/')])

    def test_resource_instance_breadcrumbs(self):
        url = '/resource/123'
        self.assertEqual(get_breadcrumbs(url), [('Root', '/'),
                                            ('Resource Root', '/resource/'),
                                            ('Resource Instance', '/resource/123')])

    def test_nested_resource_breadcrumbs(self):
        url = '/resource/123/'
        self.assertEqual(get_breadcrumbs(url), [('Root', '/'),
                                            ('Resource Root', '/resource/'),
                                            ('Resource Instance', '/resource/123'),
                                            ('Nested Resource Root', '/resource/123/')])

    def test_nested_resource_instance_breadcrumbs(self):
        url = '/resource/123/abc'
        self.assertEqual(get_breadcrumbs(url), [('Root', '/'),
                                            ('Resource Root', '/resource/'),
                                            ('Resource Instance', '/resource/123'),
                                            ('Nested Resource Root', '/resource/123/'),
                                            ('Nested Resource Instance', '/resource/123/abc')])

    def test_broken_url_breadcrumbs_handled_gracefully(self):
        url = '/foobar'
        self.assertEqual(get_breadcrumbs(url), [('Root', '/')])
