"""
Tests for content parsing, and form-overloaded content parsing.
"""
from django.conf.urls.defaults import patterns
from django.contrib.auth.models import User
from django.test import TestCase, Client
from djangorestframework import status
from djangorestframework.authentication import UserLoggedInAuthentication
from djangorestframework.compat import RequestFactory
from djangorestframework.mixins import RequestMixin
from djangorestframework.parsers import FormParser, MultiPartParser, PlainTextParser
from djangorestframework.response import Response
from djangorestframework.views import View

class MockView(View):
    authentication = (UserLoggedInAuthentication,)
    def post(self, request):
        if request.POST.get('example') is not None:
            return Response(status.OK)
        
        return Response(status.INTERNAL_SERVER_ERROR)

urlpatterns = patterns('',
    (r'^$', MockView.as_view()),
)

class TestContentParsing(TestCase):
    def setUp(self):
        self.req = RequestFactory()

    def ensure_determines_no_content_GET(self, view):
        """Ensure view.DATA returns None for GET request with no content."""
        view.request = self.req.get('/')
        self.assertEqual(view.DATA, None)

    def ensure_determines_no_content_HEAD(self, view):
        """Ensure view.DATA returns None for HEAD request."""
        view.request = self.req.head('/')
        self.assertEqual(view.DATA, None)

    def ensure_determines_form_content_POST(self, view):
        """Ensure view.DATA returns content for POST request with form content."""
        form_data = {'qwerty': 'uiop'}
        view.parsers = (FormParser, MultiPartParser)
        view.request = self.req.post('/', data=form_data)
        self.assertEqual(view.DATA.items(), form_data.items())

    def ensure_determines_non_form_content_POST(self, view):
        """Ensure view.RAW_CONTENT returns content for POST request with non-form content."""
        content = 'qwerty'
        content_type = 'text/plain'
        view.parsers = (PlainTextParser,)
        view.request = self.req.post('/', content, content_type=content_type)
        self.assertEqual(view.DATA, content)

    def ensure_determines_form_content_PUT(self, view):
        """Ensure view.RAW_CONTENT returns content for PUT request with form content."""
        form_data = {'qwerty': 'uiop'}
        view.parsers = (FormParser, MultiPartParser)
        view.request = self.req.put('/', data=form_data)
        self.assertEqual(view.DATA.items(), form_data.items())

    def ensure_determines_non_form_content_PUT(self, view):
        """Ensure view.RAW_CONTENT returns content for PUT request with non-form content."""
        content = 'qwerty'
        content_type = 'text/plain'
        view.parsers = (PlainTextParser,)
        view.request = self.req.post('/', content, content_type=content_type)
        self.assertEqual(view.DATA, content)

    def test_standard_behaviour_determines_no_content_GET(self):
        """Ensure view.DATA returns None for GET request with no content."""
        self.ensure_determines_no_content_GET(RequestMixin())

    def test_standard_behaviour_determines_no_content_HEAD(self):
        """Ensure view.DATA returns None for HEAD request."""
        self.ensure_determines_no_content_HEAD(RequestMixin())

    def test_standard_behaviour_determines_form_content_POST(self):
        """Ensure view.DATA returns content for POST request with form content."""
        self.ensure_determines_form_content_POST(RequestMixin())

    def test_standard_behaviour_determines_non_form_content_POST(self):
        """Ensure view.DATA returns content for POST request with non-form content."""
        self.ensure_determines_non_form_content_POST(RequestMixin())

    def test_standard_behaviour_determines_form_content_PUT(self):
        """Ensure view.DATA returns content for PUT request with form content."""
        self.ensure_determines_form_content_PUT(RequestMixin())

    def test_standard_behaviour_determines_non_form_content_PUT(self):
        """Ensure view.DATA returns content for PUT request with non-form content."""
        self.ensure_determines_non_form_content_PUT(RequestMixin())

    def test_overloaded_behaviour_allows_content_tunnelling(self):
        """Ensure request.DATA returns content for overloaded POST request"""
        content = 'qwerty'
        content_type = 'text/plain'
        view = RequestMixin()
        form_data = {view._CONTENT_PARAM: content,
                     view._CONTENTTYPE_PARAM: content_type}
        view.request = self.req.post('/', form_data)
        view.parsers = (PlainTextParser,)
        self.assertEqual(view.DATA, content)

class TestContentParsingWithAuthentication(TestCase):
    urls = 'djangorestframework.tests.content'
    
    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)
        self.req = RequestFactory()
    
    def test_user_logged_in_authentication_has_post_when_not_logged_in(self):
        """Ensures request.POST exists after UserLoggedInAuthentication when user doesn't log in"""
        content = {'example': 'example'}
        
        response = self.client.post('/', content)
        self.assertEqual(status.OK, response.status_code)
        
        response = self.csrf_client.post('/', content)
        self.assertEqual(status.OK, response.status_code)
    
    def test_user_logged_in_authentication_has_post_when_logged_in(self):
        """Ensures request.POST exists after UserLoggedInAuthentication when user does log in"""
        self.client.login(username='john', password='password')
        self.csrf_client.login(username='john', password='password')
        content = {'example': 'example'}
        
        response = self.client.post('/', content)
        self.assertEqual(status.OK, response.status_code, "POST data")
        
        response = self.csrf_client.post('/', content)
        self.assertEqual(status.OK, response.status_code)
