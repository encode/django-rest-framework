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
from djangorestframework.parsers import FormParser, MultiPartParser, \
    PlainTextParser, JSONParser
from djangorestframework.response import Response
from djangorestframework.request import Request
from djangorestframework.views import View
from djangorestframework.request import request_class_factory

class MockView(View):
    authentication = (UserLoggedInAuthentication,)
    def post(self, request):
        if request.POST.get('example') is not None:
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.INTERNAL_SERVER_ERROR)

urlpatterns = patterns('',
    (r'^$', MockView.as_view()),
)

request_class = request_class_factory(RequestFactory().get('/'))


class RequestTestCase(TestCase):

    def tearDown(self):
        request_class.parsers = ()

    def build_request(self, method, *args, **kwargs):
        factory = RequestFactory()
        method = getattr(factory, method)
        original_request = method(*args, **kwargs)
        return request_class(original_request)


class TestMethodOverloading(RequestTestCase):

    def test_standard_behaviour_determines_GET(self):
        """GET requests identified"""
        request = self.build_request('get', '/')
        self.assertEqual(request.method, 'GET')

    def test_standard_behaviour_determines_POST(self):
        """POST requests identified"""
        request = self.build_request('post', '/')
        self.assertEqual(request.method, 'POST')

    def test_overloaded_POST_behaviour_determines_overloaded_method(self):
        """POST requests can be overloaded to another method by setting a reserved form field"""
        request = self.build_request('post', '/', {Request._METHOD_PARAM: 'DELETE'})
        self.assertEqual(request.method, 'DELETE')

    def test_HEAD_is_a_valid_method(self):
        """HEAD requests identified"""
        request = request = self.build_request('head', '/')
        self.assertEqual(request.method, 'HEAD')


class TestContentParsing(RequestTestCase):

    def tearDown(self):
        request_class.parsers = ()

    def build_request(self, method, *args, **kwargs):
        factory = RequestFactory()
        method = getattr(factory, method)
        original_request = method(*args, **kwargs)
        return request_class(original_request)
    
    def test_standard_behaviour_determines_no_content_GET(self):
        """Ensure request.DATA returns None for GET request with no content."""
        request = self.build_request('get', '/')
        self.assertEqual(request.DATA, None)

    def test_standard_behaviour_determines_no_content_HEAD(self):
        """Ensure request.DATA returns None for HEAD request."""
        request = self.build_request('head', '/')
        self.assertEqual(request.DATA, None)

    def test_standard_behaviour_determines_form_content_POST(self):
        """Ensure request.DATA returns content for POST request with form content."""
        form_data = {'qwerty': 'uiop'}
        request_class.parsers = (FormParser, MultiPartParser)
        request = self.build_request('post', '/', data=form_data)
        self.assertEqual(request.DATA.items(), form_data.items())

    def test_standard_behaviour_determines_non_form_content_POST(self):
        """Ensure request.DATA returns content for POST request with non-form content."""
        content = 'qwerty'
        content_type = 'text/plain'
        request_class.parsers = (PlainTextParser,)
        request = self.build_request('post', '/', content, content_type=content_type)
        self.assertEqual(request.DATA, content)

    def test_standard_behaviour_determines_form_content_PUT(self):
        """Ensure request.DATA returns content for PUT request with form content."""
        form_data = {'qwerty': 'uiop'}
        request_class.parsers = (FormParser, MultiPartParser)
        request = self.build_request('put', '/', data=form_data)
        self.assertEqual(request.DATA.items(), form_data.items())

    def test_standard_behaviour_determines_non_form_content_PUT(self):
        """Ensure request.DATA returns content for PUT request with non-form content."""
        content = 'qwerty'
        content_type = 'text/plain'
        request_class.parsers = (PlainTextParser,)
        request = self.build_request('put', '/', content, content_type=content_type)
        self.assertEqual(request.DATA, content)

    def test_overloaded_behaviour_allows_content_tunnelling(self):
        """Ensure request.DATA returns content for overloaded POST request"""
        content = 'qwerty'
        content_type = 'text/plain'
        form_data = {Request._CONTENT_PARAM: content,
                     Request._CONTENTTYPE_PARAM: content_type}
        request_class.parsers = (PlainTextParser,)
        request = self.build_request('post', '/', form_data)
        self.assertEqual(request.DATA, content)

    def test_accessing_post_after_data_form(self):
        """Ensures request.POST can be accessed after request.DATA in form request"""
        form_data = {'qwerty': 'uiop'}
        request_class.parsers = (FormParser, MultiPartParser)
        request = self.build_request('post', '/', data=form_data)

        self.assertEqual(request.DATA.items(), form_data.items())
        self.assertEqual(request.POST.items(), form_data.items())

    def test_accessing_post_after_data_for_json(self):
        """Ensures request.POST can be accessed after request.DATA in json request"""
        from django.utils import simplejson as json

        data = {'qwerty': 'uiop'}
        content = json.dumps(data)
        content_type = 'application/json'

        request_class.parsers = (JSONParser,)

        request = self.build_request('post', '/', content, content_type=content_type)

        self.assertEqual(request.DATA.items(), data.items())
        self.assertEqual(request.POST.items(), [])

    def test_accessing_post_after_data_for_overloaded_json(self):
        """Ensures request.POST can be accessed after request.DATA in overloaded json request"""
        from django.utils import simplejson as json

        data = {'qwerty': 'uiop'}
        content = json.dumps(data)
        content_type = 'application/json'

        request_class.parsers = (JSONParser,)

        form_data = {Request._CONTENT_PARAM: content,
                     Request._CONTENTTYPE_PARAM: content_type}

        request = self.build_request('post', '/', data=form_data)

        self.assertEqual(request.DATA.items(), data.items())
        self.assertEqual(request.POST.items(), form_data.items())

    def test_accessing_data_after_post_form(self):
        """Ensures request.DATA can be accessed after request.POST in form request"""
        form_data = {'qwerty': 'uiop'}
        request_class.parsers = (FormParser, MultiPartParser)
        request = self.build_request('post', '/', data=form_data)

        self.assertEqual(request.POST.items(), form_data.items())
        self.assertEqual(request.DATA.items(), form_data.items())

    def test_accessing_data_after_post_for_json(self):
        """Ensures request.DATA can be accessed after request.POST in json request"""
        from django.utils import simplejson as json

        data = {'qwerty': 'uiop'}
        content = json.dumps(data)
        content_type = 'application/json'

        request_class.parsers = (JSONParser,)

        request = self.build_request('post', '/', content, content_type=content_type)

        post_items = request.POST.items()

        self.assertEqual(len(post_items), 1)
        self.assertEqual(len(post_items[0]), 2)
        self.assertEqual(post_items[0][0], content)
        self.assertEqual(request.DATA.items(), data.items())

    def test_accessing_data_after_post_for_overloaded_json(self):
        """Ensures request.DATA can be accessed after request.POST in overloaded json request"""
        from django.utils import simplejson as json

        data = {'qwerty': 'uiop'}
        content = json.dumps(data)
        content_type = 'application/json'

        request_class.parsers = (JSONParser,)

        form_data = {Request._CONTENT_PARAM: content,
                     Request._CONTENTTYPE_PARAM: content_type}

        request = self.build_request('post', '/', data=form_data)
        self.assertEqual(request.POST.items(), form_data.items())
        self.assertEqual(request.DATA.items(), data.items())


class TestContentParsingWithAuthentication(TestCase):
    urls = 'djangorestframework.tests.request'

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
