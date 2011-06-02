from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from django.test import Client


urlpatterns = patterns('djangorestframework.utils.staticviews',
    url(r'^robots.txt$', 'deny_robots'),
    url(r'^favicon.ico$', 'favicon'),
    url(r'^accounts/login$', 'api_login'),
    url(r'^accounts/logout$', 'api_logout'),
)


class ViewTests(TestCase):
    """Test the extra views djangorestframework provides"""
    urls = 'djangorestframework.tests.views'  

    def test_robots_view(self):
        """Ensure the robots view exists"""
        response = self.client.get('/robots.txt')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_favicon_view(self):
        """Ensure the favicon view exists"""
        response = self.client.get('/favicon.ico')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/vnd.microsoft.icon')

    def test_login_view(self):
        """Ensure the login view exists"""
        response = self.client.get('/accounts/login')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'].split(';')[0], 'text/html')

    def test_logout_view(self):
        """Ensure the logout view exists"""
        response = self.client.get('/accounts/logout')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'].split(';')[0], 'text/html')

    
    # TODO: Add login/logout behaviour tests
