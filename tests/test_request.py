"""
Tests for content parsing, and form-overloaded content parsing.
"""
from __future__ import unicode_literals

from django.conf.urls import url
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import six

from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.compat import is_anonymous
from rest_framework.parsers import BaseParser, FormParser, MultiPartParser
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

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


class TestContentParsing(TestCase):
    def test_standard_behaviour_determines_no_content_GET(self):
        """
        Ensure request.data returns empty QueryDict for GET request.
        """
        request = Request(factory.get('/'))
        assert request.data == {}

    def test_standard_behaviour_determines_no_content_HEAD(self):
        """
        Ensure request.data returns empty QueryDict for HEAD request.
        """
        request = Request(factory.head('/'))
        assert request.data == {}

    def test_request_DATA_with_form_content(self):
        """
        Ensure request.data returns content for POST request with form content.
        """
        data = {'qwerty': 'uiop'}
        request = Request(factory.post('/', data))
        request.parsers = (FormParser(), MultiPartParser())
        assert list(request.data.items()) == list(data.items())

    def test_request_DATA_with_text_content(self):
        """
        Ensure request.data returns content for POST request with
        non-form content.
        """
        content = six.b('qwerty')
        content_type = 'text/plain'
        request = Request(factory.post('/', content, content_type=content_type))
        request.parsers = (PlainTextParser(),)
        assert request.data == content

    def test_request_POST_with_form_content(self):
        """
        Ensure request.POST returns content for POST request with form content.
        """
        data = {'qwerty': 'uiop'}
        request = Request(factory.post('/', data))
        request.parsers = (FormParser(), MultiPartParser())
        assert list(request.POST.items()) == list(data.items())

    def test_request_POST_with_files(self):
        """
        Ensure request.POST returns no content for POST request with file content.
        """
        upload = SimpleUploadedFile("file.txt", b"file_content")
        request = Request(factory.post('/', {'upload': upload}))
        request.parsers = (FormParser(), MultiPartParser())
        assert list(request.POST.keys()) == []
        assert list(request.FILES.keys()) == ['upload']

    def test_standard_behaviour_determines_form_content_PUT(self):
        """
        Ensure request.data returns content for PUT request with form content.
        """
        data = {'qwerty': 'uiop'}
        request = Request(factory.put('/', data))
        request.parsers = (FormParser(), MultiPartParser())
        assert list(request.data.items()) == list(data.items())

    def test_standard_behaviour_determines_non_form_content_PUT(self):
        """
        Ensure request.data returns content for PUT request with
        non-form content.
        """
        content = six.b('qwerty')
        content_type = 'text/plain'
        request = Request(factory.put('/', content, content_type=content_type))
        request.parsers = (PlainTextParser(), )
        assert request.data == content


class MockView(APIView):
    authentication_classes = (SessionAuthentication,)

    def post(self, request):
        if request.POST.get('example') is not None:
            return Response(status=status.HTTP_200_OK)

        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

urlpatterns = [
    url(r'^$', MockView.as_view()),
]


@override_settings(ROOT_URLCONF='tests.test_request')
class TestContentParsingWithAuthentication(TestCase):
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
        assert status.HTTP_200_OK == response.status_code

        response = self.csrf_client.post('/', content)
        assert status.HTTP_200_OK == response.status_code


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
        assert self.request.user == self.user

    def test_user_can_login(self):
        login(self.request, self.user)
        assert self.request.user == self.user

    def test_user_can_logout(self):
        self.request.user = self.user
        self.assertFalse(is_anonymous(self.request.user))
        logout(self.request)
        self.assertTrue(is_anonymous(self.request.user))

    def test_logged_in_user_is_set_on_wrapped_request(self):
        login(self.request, self.user)
        assert self.wrapped_request.user == self.user

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
            assert str(error) in (
                "'module' object has no attribute 'MISSPELLED_NAME_THAT_DOESNT_EXIST'",  # Python < 3.5
                "module 'rest_framework' has no attribute 'MISSPELLED_NAME_THAT_DOESNT_EXIST'",  # Python >= 3.5
            )
        else:
            assert False, 'AttributeError not raised'


class TestAuthSetter(TestCase):
    def test_auth_can_be_set(self):
        request = Request(factory.get('/'))
        request.auth = 'DUMMY'
        assert request.auth == 'DUMMY'


class TestSecure(TestCase):

    def test_default_secure_false(self):
        request = Request(factory.get('/', secure=False))
        assert request.scheme == 'http'

    def test_default_secure_true(self):
        request = Request(factory.get('/', secure=True))
        assert request.scheme == 'https'
