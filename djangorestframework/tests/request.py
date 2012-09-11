"""
Tests for content parsing, and form-overloaded content parsing.
"""
from django.conf.urls.defaults import patterns
from django.contrib.auth.models import User
from django.test import TestCase, Client

from djangorestframework import status
from djangorestframework.authentication import SessionAuthentication
from djangorestframework.utils import RequestFactory
from djangorestframework.parsers import (
    FormParser,
    MultiPartParser,
    PlainTextParser,
)
from djangorestframework.request import Request
from djangorestframework.response import Response
from djangorestframework.views import APIView


factory = RequestFactory()


class TestMethodOverloading(TestCase):
    def test_GET_method(self):
        """
        GET requests identified.
        """
        request = factory.get('/')
        self.assertEqual(request.method, 'GET')

    def test_POST_method(self):
        """
        POST requests identified.
        """
        request = factory.post('/')
        self.assertEqual(request.method, 'POST')

    def test_HEAD_method(self):
        """
        HEAD requests identified.
        """
        request = factory.head('/')
        self.assertEqual(request.method, 'HEAD')

    def test_overloaded_method(self):
        """
        POST requests can be overloaded to another method by setting a
        reserved form field
        """
        request = factory.post('/', {Request._METHOD_PARAM: 'DELETE'})
        self.assertEqual(request.method, 'DELETE')


class TestContentParsing(TestCase):
    def test_standard_behaviour_determines_no_content_GET(self):
        """
        Ensure request.DATA returns None for GET request with no content.
        """
        request = factory.get('/')
        self.assertEqual(request.DATA, None)

    def test_standard_behaviour_determines_no_content_HEAD(self):
        """
        Ensure request.DATA returns None for HEAD request.
        """
        request = factory.head('/')
        self.assertEqual(request.DATA, None)

    def test_standard_behaviour_determines_form_content_POST(self):
        """
        Ensure request.DATA returns content for POST request with form content.
        """
        data = {'qwerty': 'uiop'}
        parsers = (FormParser, MultiPartParser)
        request = factory.post('/', data, parser=parsers)
        self.assertEqual(request.DATA.items(), data.items())

    def test_standard_behaviour_determines_non_form_content_POST(self):
        """
        Ensure request.DATA returns content for POST request with
        non-form content.
        """
        content = 'qwerty'
        content_type = 'text/plain'
        parsers = (PlainTextParser,)
        request = factory.post('/', content, content_type=content_type,
                               parsers=parsers)
        self.assertEqual(request.DATA, content)

    def test_standard_behaviour_determines_form_content_PUT(self):
        """
        Ensure request.DATA returns content for PUT request with form content.
        """
        data = {'qwerty': 'uiop'}
        parsers = (FormParser, MultiPartParser)

        from django import VERSION

        if VERSION >= (1, 5):
            from django.test.client import MULTIPART_CONTENT, BOUNDARY, encode_multipart
            request = factory.put('/', encode_multipart(BOUNDARY, data), parsers=parsers,
                                  content_type=MULTIPART_CONTENT)
        else:
            request = factory.put('/', data, parsers=parsers)

        self.assertEqual(request.DATA.items(), data.items())

    def test_standard_behaviour_determines_non_form_content_PUT(self):
        """
        Ensure request.DATA returns content for PUT request with
        non-form content.
        """
        content = 'qwerty'
        content_type = 'text/plain'
        parsers = (PlainTextParser, )
        request = factory.put('/', content, content_type=content_type,
                              parsers=parsers)
        self.assertEqual(request.DATA, content)

    def test_overloaded_behaviour_allows_content_tunnelling(self):
        """
        Ensure request.DATA returns content for overloaded POST request.
        """
        content = 'qwerty'
        content_type = 'text/plain'
        data = {
            Request._CONTENT_PARAM: content,
            Request._CONTENTTYPE_PARAM: content_type
        }
        parsers = (PlainTextParser, )
        request = factory.post('/', data, parsers=parsers)
        self.assertEqual(request.DATA, content)

    # def test_accessing_post_after_data_form(self):
    #     """
    #     Ensures request.POST can be accessed after request.DATA in
    #     form request.
    #     """
    #     data = {'qwerty': 'uiop'}
    #     request = factory.post('/', data=data)
    #     self.assertEqual(request.DATA.items(), data.items())
    #     self.assertEqual(request.POST.items(), data.items())

    # def test_accessing_post_after_data_for_json(self):
    #     """
    #     Ensures request.POST can be accessed after request.DATA in
    #     json request.
    #     """
    #     data = {'qwerty': 'uiop'}
    #     content = json.dumps(data)
    #     content_type = 'application/json'
    #     parsers = (JSONParser, )

    #     request = factory.post('/', content, content_type=content_type,
    #                            parsers=parsers)
    #     self.assertEqual(request.DATA.items(), data.items())
    #     self.assertEqual(request.POST.items(), [])

    # def test_accessing_post_after_data_for_overloaded_json(self):
    #     """
    #     Ensures request.POST can be accessed after request.DATA in overloaded
    #     json request.
    #     """
    #     data = {'qwerty': 'uiop'}
    #     content = json.dumps(data)
    #     content_type = 'application/json'
    #     parsers = (JSONParser, )
    #     form_data = {Request._CONTENT_PARAM: content,
    #                  Request._CONTENTTYPE_PARAM: content_type}

    #     request = factory.post('/', form_data, parsers=parsers)
    #     self.assertEqual(request.DATA.items(), data.items())
    #     self.assertEqual(request.POST.items(), form_data.items())

    # def test_accessing_data_after_post_form(self):
    #     """
    #     Ensures request.DATA can be accessed after request.POST in
    #     form request.
    #     """
    #     data = {'qwerty': 'uiop'}
    #     parsers = (FormParser, MultiPartParser)
    #     request = factory.post('/', data, parsers=parsers)

    #     self.assertEqual(request.POST.items(), data.items())
    #     self.assertEqual(request.DATA.items(), data.items())

    # def test_accessing_data_after_post_for_json(self):
    #     """
    #     Ensures request.DATA can be accessed after request.POST in
    #     json request.
    #     """
    #     data = {'qwerty': 'uiop'}
    #     content = json.dumps(data)
    #     content_type = 'application/json'
    #     parsers = (JSONParser, )
    #     request = factory.post('/', content, content_type=content_type,
    #                            parsers=parsers)
    #     self.assertEqual(request.POST.items(), [])
    #     self.assertEqual(request.DATA.items(), data.items())

    # def test_accessing_data_after_post_for_overloaded_json(self):
    #     """
    #     Ensures request.DATA can be accessed after request.POST in overloaded
    #     json request
    #     """
    #     data = {'qwerty': 'uiop'}
    #     content = json.dumps(data)
    #     content_type = 'application/json'
    #     parsers = (JSONParser, )
    #     form_data = {Request._CONTENT_PARAM: content,
    #                  Request._CONTENTTYPE_PARAM: content_type}

    #     request = factory.post('/', form_data, parsers=parsers)
    #     self.assertEqual(request.POST.items(), form_data.items())
    #     self.assertEqual(request.DATA.items(), data.items())


class MockView(APIView):
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        if request.POST.get('example') is not None:
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.INTERNAL_SERVER_ERROR)

urlpatterns = patterns('',
    (r'^$', MockView.as_view()),
)


class TestContentParsingWithAuthentication(TestCase):
    urls = 'djangorestframework.tests.request'

    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(self.username, self.email, self.password)

    def test_user_logged_in_authentication_has_POST_when_not_logged_in(self):
        """
        Ensures request.POST exists after SessionAuthentication when user
        doesn't log in.
        """
        content = {'example': 'example'}

        response = self.client.post('/', content)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

        response = self.csrf_client.post('/', content)
        self.assertEqual(status.HTTP_200_OK, response.status_code)

    # def test_user_logged_in_authentication_has_post_when_logged_in(self):
    #     """Ensures request.POST exists after UserLoggedInAuthentication when user does log in"""
    #     self.client.login(username='john', password='password')
    #     self.csrf_client.login(username='john', password='password')
    #     content = {'example': 'example'}

    #     response = self.client.post('/', content)
    #     self.assertEqual(status.OK, response.status_code, "POST data is malformed")

    #     response = self.csrf_client.post('/', content)
    #     self.assertEqual(status.OK, response.status_code, "POST data is malformed")
