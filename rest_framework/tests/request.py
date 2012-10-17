"""
Tests for content parsing, and form-overloaded content parsing.
"""
from django.conf.urls.defaults import patterns
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.utils import simplejson as json

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from django.test.client import RequestFactory
from rest_framework.parsers import (
    BaseParser,
    FormParser,
    MultiPartParser,
    JSONParser
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView


factory = RequestFactory()


class PlainTextParser(BaseParser):
    media_type = 'text/plain'

    def parse(self, stream, media_type=None, parser_context=None):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will simply be a string representing the body of the request.
        `files` will always be `None`.
        """
        return stream.read()


class TestMethodOverloading(TestCase):
    def test_method(self):
        """
        Request methods should be same as underlying request.
        """
        request = Request(factory.get('/'))
        self.assertEqual(request.method, 'GET')
        request = Request(factory.post('/'))
        self.assertEqual(request.method, 'POST')

    def test_overloaded_method(self):
        """
        POST requests can be overloaded to another method by setting a
        reserved form field
        """
        request = Request(factory.post('/', {api_settings.FORM_METHOD_OVERRIDE: 'DELETE'}))
        self.assertEqual(request.method, 'DELETE')


class TestContentParsing(TestCase):
    def test_standard_behaviour_determines_no_content_GET(self):
        """
        Ensure request.DATA returns None for GET request with no content.
        """
        request = Request(factory.get('/'))
        self.assertEqual(request.DATA, None)

    def test_standard_behaviour_determines_no_content_HEAD(self):
        """
        Ensure request.DATA returns None for HEAD request.
        """
        request = Request(factory.head('/'))
        self.assertEqual(request.DATA, None)

    def test_request_DATA_with_form_content(self):
        """
        Ensure request.DATA returns content for POST request with form content.
        """
        data = {'qwerty': 'uiop'}
        request = Request(factory.post('/', data))
        request.parsers = (FormParser(), MultiPartParser())
        self.assertEqual(request.DATA.items(), data.items())

    def test_request_DATA_with_text_content(self):
        """
        Ensure request.DATA returns content for POST request with
        non-form content.
        """
        content = 'qwerty'
        content_type = 'text/plain'
        request = Request(factory.post('/', content, content_type=content_type))
        request.parsers = (PlainTextParser(),)
        self.assertEqual(request.DATA, content)

    def test_request_POST_with_form_content(self):
        """
        Ensure request.POST returns content for POST request with form content.
        """
        data = {'qwerty': 'uiop'}
        request = Request(factory.post('/', data))
        request.parsers = (FormParser(), MultiPartParser())
        self.assertEqual(request.POST.items(), data.items())

    def test_standard_behaviour_determines_form_content_PUT(self):
        """
        Ensure request.DATA returns content for PUT request with form content.
        """
        data = {'qwerty': 'uiop'}

        from django import VERSION

        if VERSION >= (1, 5):
            from django.test.client import MULTIPART_CONTENT, BOUNDARY, encode_multipart
            request = Request(factory.put('/', encode_multipart(BOUNDARY, data),
                                  content_type=MULTIPART_CONTENT))
        else:
            request = Request(factory.put('/', data))

        request.parsers = (FormParser(), MultiPartParser())
        self.assertEqual(request.DATA.items(), data.items())

    def test_standard_behaviour_determines_non_form_content_PUT(self):
        """
        Ensure request.DATA returns content for PUT request with
        non-form content.
        """
        content = 'qwerty'
        content_type = 'text/plain'
        request = Request(factory.put('/', content, content_type=content_type))
        request.parsers = (PlainTextParser(), )
        self.assertEqual(request.DATA, content)

    def test_overloaded_behaviour_allows_content_tunnelling(self):
        """
        Ensure request.DATA returns content for overloaded POST request.
        """
        json_data = {'foobar': 'qwerty'}
        content = json.dumps(json_data)
        content_type = 'application/json'
        form_data = {
            api_settings.FORM_CONTENT_OVERRIDE: content,
            api_settings.FORM_CONTENTTYPE_OVERRIDE: content_type
        }
        request = Request(factory.post('/', form_data))
        request.parsers = (JSONParser(), )
        self.assertEqual(request.DATA, json_data)

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
    urls = 'rest_framework.tests.request'

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
