from django.conf.urls.defaults import patterns
from django.test import TestCase
from django.utils import simplejson as json

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


#class ThrottlingTests(TestCase):
#    """Basic authentication"""
#    urls = 'djangorestframework.tests.throttling'      
#
#    def test_requests_are_throttled(self):
#        """Ensure request rate is limited"""
#        for dummy in range(3):
#            response = self.client.get('/')
#        response = self.client.get('/')
#        
#    def test_request_throttling_is_per_user(self):
#        """Ensure request rate is only limited per user, not globally"""
#        pass
#    
#    def test_request_throttling_expires(self):
#        """Ensure request rate is limited for a limited duration only"""
#        pass
