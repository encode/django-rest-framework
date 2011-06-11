import time

from django.conf.urls.defaults import patterns
from django.test import TestCase
from django.utils import simplejson as json
from django.contrib.auth.models import User
from django.core.cache import cache

from djangorestframework.compat import RequestFactory
from djangorestframework.views import View
from djangorestframework.permissions import PerUserThrottling, PerViewThrottling, PerResourceThrottling, ConfigurationException
from djangorestframework.resources import FormResource

class MockView(View):
    permissions = ( PerUserThrottling, )
    throttle = '3/sec' # 3 requests per second

    def get(self, request):
        return 'foo'

class MockView1(MockView):
    permissions = ( PerViewThrottling, )

class MockView2(MockView):
    permissions = ( PerResourceThrottling, )
    #No resource set
    
class MockView3(MockView2):    
    resource = FormResource
    
class ThrottlingTests(TestCase):
    urls = 'djangorestframework.tests.throttling'   
    
    def setUp(self):
        """Reset the cache so that no throttles will be active"""
        cache.clear()
        self.factory = RequestFactory()
        
    def test_requests_are_throttled(self):
        """Ensure request rate is limited"""
        request = self.factory.get('/')
        for dummy in range(4):
            response = MockView.as_view()(request)
        self.assertEqual(503, response.status_code)
        
    def test_request_throttling_expires(self):
        """Ensure request rate is limited for a limited duration only"""
        request = self.factory.get('/')
        for dummy in range(4):
            response = MockView.as_view()(request)
        self.assertEqual(503, response.status_code)
        time.sleep(1)
        response = MockView.as_view()(request)
        self.assertEqual(200, response.status_code)
        
    def ensure_is_throttled(self, view):
        request = self.factory.get('/')
        request.user = User.objects.create(username='a')
        for dummy in range(3):
            response = view.as_view()(request)
        request.user = User.objects.create(username='b')
        response = view.as_view()(request)
        self.assertEqual(503, response.status_code)
        
    def test_request_throttling_is_per_user(self):
        """Ensure request rate is only limited per user, not globally for PerUserTrottles"""
        self.ensure_is_throttled(MockView)
        
    def test_request_throttling_is_per_view(self):
        """Ensure request rate is limited globally per View for PerViewThrottles"""
        self.ensure_is_throttled(MockView1)
        
    def test_request_throttling_is_per_resource(self):
        """Ensure request rate is limited globally per Resource for PerResourceThrottles"""        
        self.ensure_is_throttled(MockView3)

    def test_raises_no_resource_found(self):
        """Ensure an Exception is raised when someone sets at per-resource throttle
        on a view with no resource set."""
        request = self.factory.get('/')
        view = MockView2.as_view()
        self.assertRaises(ConfigurationException, view, request)
        
    