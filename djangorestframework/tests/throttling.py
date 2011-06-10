import time

from django.conf.urls.defaults import patterns
from django.test import TestCase
from django.utils import simplejson as json
from django.contrib.auth.models import User

from djangorestframework.compat import RequestFactory
from djangorestframework.views import View
from djangorestframework.permissions import PerUserThrottling


class MockView(View):
    permissions = ( PerUserThrottling, )
    throttle = (3, 1) # 3 requests per second

    def get(self, request):
        return 'foo'

urlpatterns = patterns('',
    (r'^$', MockView.as_view()),
)

class ThrottlingTests(TestCase):
    urls = 'djangorestframework.tests.throttling'   
    
    def setUp(self):
        time.sleep(1) # make sure throttle is expired before next test        
        
    def test_requests_are_throttled(self):
        """Ensure request rate is limited"""
        for dummy in range(3):
            response = self.client.get('/')
        response = self.client.get('/')
        self.assertEqual(503, response.status_code)
        
    def DISABLEDtest_request_throttling_is_per_user(self):
        #Can not login user.....Dunno why...
        """Ensure request rate is only limited per user, not globally"""
        User.objects.create_user('testuser', 'test', 'foo@bar.baz').save()
        User.objects.create_user('another_testuser', 'test', 'foo@bar.baz').save()

        self.assertTrue(self.client.login(username='testuser', password='test'))
        for dummy in range(3):
            response = self.client.get('/')
        self.client.logout()
        self.assertTrue(self.client.login(username='another_testuser', password='test'))
        self.assertEqual(200, response.status_code)
        
    def test_request_throttling_expires(self):
        """Ensure request rate is limited for a limited duration only"""
        for dummy in range(3):
            response = self.client.get('/')
        response = self.client.get('/')
        self.assertEqual(503, response.status_code)
        time.sleep(1)
        response = self.client.get('/')
        self.assertEqual(200, response.status_code)
