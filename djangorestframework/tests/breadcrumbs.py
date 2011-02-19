from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from djangorestframework.breadcrumbs import get_breadcrumbs
from djangorestframework.resource import Resource

class Root(Resource):
    pass

class ResourceRoot(Resource):
    pass

class ResourceInstance(Resource):
    pass

class NestedResourceRoot(Resource):
    pass

class NestedResourceInstance(Resource):
    pass

urlpatterns = patterns('',
    url(r'^$', Root),
    url(r'^resource/$', ResourceRoot),
    url(r'^resource/(?P<key>[0-9]+)$', ResourceInstance),
    url(r'^resource/(?P<key>[0-9]+)/$', NestedResourceRoot),
    url(r'^resource/(?P<key>[0-9]+)/(?P<other>[A-Za-z]+)$', NestedResourceInstance),
)


class BreadcrumbTests(TestCase):
    """Tests the breadcrumb functionality used by the HTML emitter."""

    urls = 'djangorestframework.tests.breadcrumbs'

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