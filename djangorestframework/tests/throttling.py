import time

from django.conf.urls.defaults import patterns
from django.test import TestCase
from django.utils import simplejson as json
from django.contrib.auth.models import User
from django.core.cache import cache

from djangorestframework.compat import RequestFactory
from djangorestframework.views import View
from djangorestframework.permissions import PerUserThrottling, PerResourceThrottling


class MockView(View):
    permissions = ( PerUserThrottling, )
    throttle = (3, 1) # 3 requests per second

    def get(self, request):
        return 'foo'

class MockView1(View):
    permissions = ( PerResourceThrottling, )
    throttle = (3, 1) # 3 requests per second

    def get(self, request):
        return 'foo'

urlpatterns = patterns('',
    (r'^$', MockView.as_view()),
    (r'^1$', MockView1.as_view()),
)

class ThrottlingTests(TestCase):
    urls = 'djangorestframework.tests.throttling'   
    
    def setUp(self):
        """Reset the cache so that no throttles will be active"""
        cache.clear()
        
    def test_requests_are_throttled(self):
        """Ensure request rate is limited"""
        for dummy in range(3):
            response = self.client.get('/')
        response = self.client.get('/')
        self.assertEqual(503, response.status_code)
        
    def test_request_throttling_is_per_user(self):
        """Ensure request rate is only limited per user, not globally"""
        for username in ('testuser', 'another_testuser'):
            user = User.objects.create(username=username)
            user.set_password('test')
            user.save()
        
        self.assertTrue(self.client.login(username='testuser', password='test'), msg='Login Failed')
        for dummy in range(3):
            response = self.client.get('/')
        self.client.logout()
        self.assertTrue(self.client.login(username='another_testuser', password='test'), msg='Login failed')
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
 
    def test_request_throttling_is_per_resource(self):
        """Ensure request rate is limited globally per View"""
        for username in ('testuser', 'another_testuser'):
            user = User.objects.create(username=username)
            user.set_password('test')
            user.save()
        
        self.assertTrue(self.client.login(username='testuser', password='test'), msg='Login Failed')
        for dummy in range(3):
            response = self.client.get('/1')
        self.client.logout()
        self.assertTrue(self.client.login(username='another_testuser', password='test'), msg='Login failed')
        response = self.client.get('/1')
        self.assertEqual(503, response.status_code)
        
    def test_request_throttling_expires(self):
        """Ensure request rate is limited for a limited duration only"""
        for dummy in range(3):
            response = self.client.get('/')
        response = self.client.get('/')
        self.assertEqual(503, response.status_code)
        time.sleep(1)
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
