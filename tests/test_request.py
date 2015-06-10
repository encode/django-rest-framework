"""
Tests for content parsing, and form-overloaded content parsing.
"""
from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.handlers.wsgi import WSGIRequest
from django.test import TestCase
from django.utils import six
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.parsers import (
    BaseParser,
    FormParser,
    MultiPartParser,
    JSONParser
)
from rest_framework.request import Request, Empty
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory, APIClient
from rest_framework.views import APIView
from io import BytesIO
import json


factory = APIRequestFactory()


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

    def test_x_http_method_override_header(self):
        """
        POST requests can also be overloaded to another method by setting
        the X-HTTP-Method-Override header.
        """
        request = Request(factory.post('/', {'foo': 'bar'}, HTTP_X_HTTP_METHOD_OVERRIDE='DELETE'))
        self.assertEqual(request.method, 'DELETE')

        request = Request(factory.get('/', {'foo': 'bar'}, HTTP_X_HTTP_METHOD_OVERRIDE='DELETE'))
        self.assertEqual(request.method, 'DELETE')


class TestContentParsing(TestCase):
    def test_standard_behaviour_determines_no_content_GET(self):
        """
        Ensure request.DATA returns empty QueryDict for GET request.
        """
        request = Request(factory.get('/'))
        self.assertEqual(request.DATA, {})

    def test_standard_behaviour_determines_no_content_HEAD(self):
        """
        Ensure request.DATA returns empty QueryDict for HEAD request.
        """
        request = Request(factory.head('/'))
        self.assertEqual(request.DATA, {})

    def test_request_DATA_with_form_content(self):
        """
        Ensure request.DATA returns content for POST request with form content.
        """
        data = {'qwerty': 'uiop'}
        request = Request(factory.post('/', data))
        request.parsers = (FormParser(), MultiPartParser())
        self.assertEqual(list(request.DATA.items()), list(data.items()))

    def test_request_DATA_with_text_content(self):
        """
        Ensure request.DATA returns content for POST request with
        non-form content.
        """
        content = six.b('qwerty')
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
        self.assertEqual(list(request.POST.items()), list(data.items()))

    def test_standard_behaviour_determines_form_content_PUT(self):
        """
        Ensure request.DATA returns content for PUT request with form content.
        """
        data = {'qwerty': 'uiop'}
        request = Request(factory.put('/', data))
        request.parsers = (FormParser(), MultiPartParser())
        self.assertEqual(list(request.DATA.items()), list(data.items()))

    def test_standard_behaviour_determines_non_form_content_PUT(self):
        """
        Ensure request.DATA returns content for PUT request with
        non-form content.
        """
        content = six.b('qwerty')
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

    def test_form_POST_unicode(self):
        """
        JSON POST via default web interface with unicode data
        """
        # Note: environ and other variables here have simplified content compared to real Request
        CONTENT = b'_content_type=application%2Fjson&_content=%7B%22request%22%3A+4%2C+%22firm%22%3A+1%2C+%22text%22%3A+%22%D0%9F%D1%80%D0%B8%D0%B2%D0%B5%D1%82%21%22%7D'
        environ = {
            'REQUEST_METHOD': 'POST',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'CONTENT_LENGTH': len(CONTENT),
            'wsgi.input': BytesIO(CONTENT),
        }
        wsgi_request = WSGIRequest(environ=environ)
        wsgi_request._load_post_and_files()
        parsers = (JSONParser(), FormParser(), MultiPartParser())
        parser_context = {
            'encoding': 'utf-8',
            'kwargs': {},
            'args': (),
        }
        request = Request(wsgi_request, parsers=parsers, parser_context=parser_context)
        method = request.method
        self.assertEqual(method, 'POST')
        self.assertEqual(request._content_type, 'application/json')
        self.assertEqual(request._stream.getvalue(), b'{"request": 4, "firm": 1, "text": "\xd0\x9f\xd1\x80\xd0\xb8\xd0\xb2\xd0\xb5\xd1\x82!"}')
        self.assertEqual(request._data, Empty)
        self.assertEqual(request._files, Empty)


class MockView(APIView):
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        if request.POST.get('example') is not None:
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

urlpatterns = [
    (r'^$', MockView.as_view()),
]


class TestContentParsingWithAuthentication(TestCase):
    urls = 'tests.test_request'

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
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


class TestUserSetter(TestCase):

    def setUp(self):
        # Pass request object through session middleware so session is
        # available to login and logout functions
        self.wrapped_request = factory.get('/')
        self.request = Request(self.wrapped_request)
        SessionMiddleware().process_request(self.request)

        User.objects.create_user('ringo', 'starr@thebeatles.com', 'yellow')
        self.user = authenticate(username='ringo', password='yellow')

    def test_user_can_be_set(self):
        self.request.user = self.user
        self.assertEqual(self.request.user, self.user)

    def test_user_can_login(self):
        login(self.request, self.user)
        self.assertEqual(self.request.user, self.user)

    def test_user_can_logout(self):
        self.request.user = self.user
        self.assertFalse(self.request.user.is_anonymous())
        logout(self.request)
        self.assertTrue(self.request.user.is_anonymous())

    def test_logged_in_user_is_set_on_wrapped_request(self):
        login(self.request, self.user)
        self.assertEqual(self.wrapped_request.user, self.user)

    def test_calling_user_fails_when_attribute_error_is_raised(self):
        """
        This proves that when an AttributeError is raised inside of the request.user
        property, that we can handle this and report the true, underlying error.
        """
        class AuthRaisesAttributeError(object):
            def authenticate(self, request):
                import rest_framework
                rest_framework.MISSPELLED_NAME_THAT_DOESNT_EXIST

        self.request = Request(factory.get('/'), authenticators=(AuthRaisesAttributeError(),))
        SessionMiddleware().process_request(self.request)

        login(self.request, self.user)
        try:
            self.request.user
        except AttributeError as error:
            self.assertEqual(str(error), "'module' object has no attribute 'MISSPELLED_NAME_THAT_DOESNT_EXIST'")
        else:
            assert False, 'AttributeError not raised'


class TestAuthSetter(TestCase):
    def test_auth_can_be_set(self):
        request = Request(factory.get('/'))
        request.auth = 'DUMMY'
        self.assertEqual(request.auth, 'DUMMY')
