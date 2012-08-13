"""
Tests for content parsing, and form-overloaded content parsing.
"""
from django.conf.urls.defaults import patterns
from django.contrib.auth.models import User
from django.test import TestCase, Client
from djangorestframework import status
from djangorestframework.authentication import UserLoggedInAuthentication
from djangorestframework.compat import RequestFactory, unittest
from djangorestframework.mixins import RequestMixin
from djangorestframework.parsers import FormParser, MultiPartParser, \
    PlainTextParser, JSONParser
from djangorestframework.response import Response
from djangorestframework.views import View

class MockView(View):
    authentication = (UserLoggedInAuthentication,)
    def post(self, request):
        if request.POST.get('example') is not None:
            return Response(status.HTTP_200_OK)

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

    def test_accessing_post_after_data_form(self):
        """Ensures request.POST can be accessed after request.DATA in form request"""
        form_data = {'qwerty': 'uiop'}
        view = RequestMixin()
        view.parsers = (FormParser, MultiPartParser)
        view.request = self.req.post('/', data=form_data)

        self.assertEqual(view.DATA.items(), form_data.items())
        self.assertEqual(view.request.POST.items(), form_data.items())

    @unittest.skip('This test was disabled some time ago for some reason')
    def test_accessing_post_after_data_for_json(self):
        """Ensures request.POST can be accessed after request.DATA in json request"""
        from django.utils import simplejson as json

        data = {'qwerty': 'uiop'}
        content = json.dumps(data)
        content_type = 'application/json'

        view = RequestMixin()
        view.parsers = (JSONParser,)

        view.request = self.req.post('/', content, content_type=content_type)

        self.assertEqual(view.DATA.items(), data.items())
        self.assertEqual(view.request.POST.items(), [])

    def test_accessing_post_after_data_for_overloaded_json(self):
        """Ensures request.POST can be accessed after request.DATA in overloaded json request"""
        from django.utils import simplejson as json

        data = {'qwerty': 'uiop'}
        content = json.dumps(data)
        content_type = 'application/json'

        view = RequestMixin()
        view.parsers = (JSONParser,)

        form_data = {view._CONTENT_PARAM: content,
                     view._CONTENTTYPE_PARAM: content_type}

        view.request = self.req.post('/', data=form_data)

        self.assertEqual(view.DATA.items(), data.items())
        self.assertEqual(view.request.POST.items(), form_data.items())

    def test_accessing_data_after_post_form(self):
        """Ensures request.DATA can be accessed after request.POST in form request"""
        form_data = {'qwerty': 'uiop'}
        view = RequestMixin()
        view.parsers = (FormParser, MultiPartParser)
        view.request = self.req.post('/', data=form_data)

        self.assertEqual(view.request.POST.items(), form_data.items())
        self.assertEqual(view.DATA.items(), form_data.items())

    def test_accessing_data_after_post_for_json(self):
        """Ensures request.DATA can be accessed after request.POST in json request"""
        from django.utils import simplejson as json

        data = {'qwerty': 'uiop'}
        content = json.dumps(data)
        content_type = 'application/json'

        view = RequestMixin()
        view.parsers = (JSONParser,)

        view.request = self.req.post('/', content, content_type=content_type)

        post_items = view.request.POST.items()

        self.assertEqual(len(post_items), 1)
        self.assertEqual(len(post_items[0]), 2)
        self.assertEqual(post_items[0][0], content)
        self.assertEqual(view.DATA.items(), data.items())

    def test_accessing_data_after_post_for_overloaded_json(self):
        """Ensures request.DATA can be accessed after request.POST in overloaded json request"""
        from django.utils import simplejson as json

        data = {'qwerty': 'uiop'}
        content = json.dumps(data)
        content_type = 'application/json'

        view = RequestMixin()
        view.parsers = (JSONParser,)

        form_data = {view._CONTENT_PARAM: content,
                     view._CONTENTTYPE_PARAM: content_type}

        view.request = self.req.post('/', data=form_data)

        self.assertEqual(view.request.POST.items(), form_data.items())
        self.assertEqual(view.DATA.items(), data.items())

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
        self.assertEqual(status.HTTP_200_OK, response.status_code, "POST data is malformed")

        response = self.csrf_client.post('/', content)
        self.assertEqual(status.HTTP_200_OK, response.status_code, "POST data is malformed")

    # def test_user_logged_in_authentication_has_post_when_logged_in(self):
    #     """Ensures request.POST exists after UserLoggedInAuthentication when user does log in"""
    #     self.client.login(username='john', password='password')
    #     self.csrf_client.login(username='john', password='password')
    #     content = {'example': 'example'}

    #     response = self.client.post('/', content)
    #     self.assertEqual(status.OK, response.status_code, "POST data is malformed")

    #     response = self.csrf_client.post('/', content)
    #     self.assertEqual(status.OK, response.status_code, "POST data is malformed")
