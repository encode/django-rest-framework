"""
Tests for the throttling implementations in the permissions module.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache

from djangorestframework.compat import RequestFactory
from djangorestframework.views import View
from djangorestframework.permissions import PerUserThrottling, PerViewThrottling, PerResourceThrottling
from djangorestframework.resources import FormResource

class MockView(View):
    permissions = ( PerUserThrottling, )
    throttle = '3/sec'

    def get(self, request):
        return 'foo'

class MockView_PerViewThrottling(MockView):
    permissions = ( PerViewThrottling, )

class MockView_PerResourceThrottling(MockView):    
    permissions = ( PerResourceThrottling, )
    resource = FormResource

class MockView_MinuteThrottling(MockView):
    throttle = '3/min'
 
 
    
class ThrottlingTests(TestCase):
    urls = 'djangorestframework.tests.throttling'   
    
    def setUp(self):
        """
        Reset the cache so that no throttles will be active
        """
        cache.clear()
        self.factory = RequestFactory()
        
    def test_requests_are_throttled(self):
        """
        Ensure request rate is limited
        """
        request = self.factory.get('/')
        for dummy in range(4):
            response = MockView.as_view()(request)
        self.assertEqual(503, response.status_code)
        
    def set_throttle_timer(self, view, value):
        """
        Explicitly set the timer, overriding time.time()
        """
        view.permissions[0].timer = lambda self: value

    def test_request_throttling_expires(self):
        """
        Ensure request rate is limited for a limited duration only
        """
        self.set_throttle_timer(MockView, 0)

        request = self.factory.get('/')
        for dummy in range(4):
            response = MockView.as_view()(request)
        self.assertEqual(503, response.status_code)

        # Advance the timer by one second
        self.set_throttle_timer(MockView, 1)

        response = MockView.as_view()(request)
        self.assertEqual(200, response.status_code)
        
    def ensure_is_throttled(self, view, expect):
        request = self.factory.get('/')
        request.user = User.objects.create(username='a')
        for dummy in range(3):
            view.as_view()(request)
        request.user = User.objects.create(username='b')
        response = view.as_view()(request)
        self.assertEqual(expect, response.status_code)
        
    def test_request_throttling_is_per_user(self):
        """
        Ensure request rate is only limited per user, not globally for 
        PerUserThrottles
        """
        self.ensure_is_throttled(MockView, 200)
        
    def test_request_throttling_is_per_view(self):
        """
        Ensure request rate is limited globally per View for PerViewThrottles
        """
        self.ensure_is_throttled(MockView_PerViewThrottling, 503)
        
    def test_request_throttling_is_per_resource(self):
        """
        Ensure request rate is limited globally per Resource for PerResourceThrottles
        """        
        self.ensure_is_throttled(MockView_PerResourceThrottling, 503)
        
        
    def ensure_response_header_contains_proper_throttle_field(self, view, expected_headers):
        """
        Ensure the response returns an X-Throttle field with status and next attributes
        set properly.
        """
        request = self.factory.get('/')
        for timer, expect in expected_headers:
            self.set_throttle_timer(view, timer)
            response = view.as_view()(request)
            self.assertEquals(response['X-Throttle'], expect)
            
    def test_seconds_fields(self):
        """
        Ensure for second based throttles.
        """
        self.ensure_response_header_contains_proper_throttle_field(MockView,
         ((0, 'status=SUCCESS; next=0.33 sec'),
          (0, 'status=SUCCESS; next=0.50 sec'),
          (0, 'status=SUCCESS; next=1.00 sec'),
          (0, 'status=FAILURE; next=1.00 sec')
         ))
            
    def test_minutes_fields(self):
        """
        Ensure for minute based throttles.
        """
        self.ensure_response_header_contains_proper_throttle_field(MockView_MinuteThrottling,
         ((0, 'status=SUCCESS; next=20.00 sec'),
          (0, 'status=SUCCESS; next=30.00 sec'),
          (0, 'status=SUCCESS; next=60.00 sec'),
          (0, 'status=FAILURE; next=60.00 sec')
         ))
    
    def test_next_rate_remains_constant_if_followed(self):
        """
        If a client follows the recommended next request rate,
        the throttling rate should stay constant.
        """
        self.ensure_response_header_contains_proper_throttle_field(MockView_MinuteThrottling,
         ((0, 'status=SUCCESS; next=20.00 sec'),
          (20, 'status=SUCCESS; next=20.00 sec'),
          (40, 'status=SUCCESS; next=20.00 sec'),
          (60, 'status=SUCCESS; next=20.00 sec'),
          (80, 'status=SUCCESS; next=20.00 sec')
         ))
