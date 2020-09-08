import base64

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import include, path

from rest_framework import (
    HTTP_HEADER_ENCODING, exceptions, permissions, renderers, status
)
from rest_framework.authentication import (
    BaseAuthentication, BasicAuthentication, RemoteUserAuthentication,
    SessionAuthentication, TokenAuthentication
)
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

from .models import CustomToken

factory = APIRequestFactory()


class CustomTokenAuthentication(TokenAuthentication):
    model = CustomToken


class CustomKeywordTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'


class MockView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def post(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})

    def put(self, request):
        return HttpResponse({'a': 1, 'b': 2, 'c': 3})


urlpatterns = [
    path(
        'session/',
        MockView.as_view(authentication_classes=[SessionAuthentication])
    ),
    path(
        'basic/',
        MockView.as_view(authentication_classes=[BasicAuthentication])
    ),
    path(
        'remote-user/',
        MockView.as_view(authentication_classes=[RemoteUserAuthentication])
    ),
    path(
        'token/',
        MockView.as_view(authentication_classes=[TokenAuthentication])
    ),
    path(
        'customtoken/',
        MockView.as_view(authentication_classes=[CustomTokenAuthentication])
    ),
    path(
        'customkeywordtoken/',
        MockView.as_view(
            authentication_classes=[CustomKeywordTokenAuthentication]
        )
    ),
    path('auth-token/', obtain_auth_token),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]


@override_settings(ROOT_URLCONF=__name__)
class BasicAuthTests(TestCase):
    """Basic authentication"""
    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            self.username, self.email, self.password
        )

    def test_post_form_passing_basic_auth(self):
        """Ensure POSTing json over basic auth with correct credentials passes and does not require CSRF"""
        credentials = ('%s:%s' % (self.username, self.password))
        base64_credentials = base64.b64encode(
            credentials.encode(HTTP_HEADER_ENCODING)
        ).decode(HTTP_HEADER_ENCODING)
        auth = 'Basic %s' % base64_credentials
        response = self.csrf_client.post(
            '/basic/',
            {'example': 'example'},
            HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_200_OK

    def test_post_json_passing_basic_auth(self):
        """Ensure POSTing form over basic auth with correct credentials passes and does not require CSRF"""
        credentials = ('%s:%s' % (self.username, self.password))
        base64_credentials = base64.b64encode(
            credentials.encode(HTTP_HEADER_ENCODING)
        ).decode(HTTP_HEADER_ENCODING)
        auth = 'Basic %s' % base64_credentials
        response = self.csrf_client.post(
            '/basic/',
            {'example': 'example'},
            format='json',
            HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_200_OK

    def test_regression_handle_bad_base64_basic_auth_header(self):
        """Ensure POSTing JSON over basic auth with incorrectly padded Base64 string is handled correctly"""
        # regression test for issue in 'rest_framework.authentication.BasicAuthentication.authenticate'
        # https://github.com/encode/django-rest-framework/issues/4089
        auth = 'Basic =a='
        response = self.csrf_client.post(
            '/basic/',
            {'example': 'example'},
            format='json',
            HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_form_failing_basic_auth(self):
        """Ensure POSTing form over basic auth without correct credentials fails"""
        response = self.csrf_client.post('/basic/', {'example': 'example'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_json_failing_basic_auth(self):
        """Ensure POSTing json over basic auth without correct credentials fails"""
        response = self.csrf_client.post(
            '/basic/',
            {'example': 'example'},
            format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response['WWW-Authenticate'] == 'Basic realm="api"'

    def test_fail_post_if_credentials_are_missing(self):
        response = self.csrf_client.post(
            '/basic/', {'example': 'example'}, HTTP_AUTHORIZATION='Basic ')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_if_credentials_contain_spaces(self):
        response = self.csrf_client.post(
            '/basic/', {'example': 'example'},
            HTTP_AUTHORIZATION='Basic foo bar'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_decoding_of_utf8_credentials(self):
        username = 'walterwhité'
        email = 'walterwhite@example.com'
        password = 'pässwörd'
        User.objects.create_user(
            username, email, password
        )
        credentials = ('%s:%s' % (username, password))
        base64_credentials = base64.b64encode(
            credentials.encode('utf-8')
        ).decode(HTTP_HEADER_ENCODING)
        auth = 'Basic %s' % base64_credentials
        response = self.csrf_client.post(
            '/basic/',
            {'example': 'example'},
            HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_200_OK


@override_settings(ROOT_URLCONF=__name__)
class SessionAuthTests(TestCase):
    """User session authentication"""
    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.non_csrf_client = APIClient(enforce_csrf_checks=False)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            self.username, self.email, self.password
        )

    def tearDown(self):
        self.csrf_client.logout()

    def test_login_view_renders_on_get(self):
        """
        Ensure the login template renders for a basic GET.

        cf. [#1810](https://github.com/encode/django-rest-framework/pull/1810)
        """
        response = self.csrf_client.get('/auth/login/')
        content = response.content.decode()
        assert '<label for="id_username">Username:</label>' in content

    def test_post_form_session_auth_failing_csrf(self):
        """
        Ensure POSTing form over session authentication without CSRF token fails.
        """
        self.csrf_client.login(username=self.username, password=self.password)
        response = self.csrf_client.post('/session/', {'example': 'example'})
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_post_form_session_auth_passing_csrf(self):
        """
        Ensure POSTing form over session authentication with CSRF token succeeds.
        Regression test for #6088
        """
        from django.middleware.csrf import _get_new_csrf_token

        self.csrf_client.login(username=self.username, password=self.password)

        # Set the csrf_token cookie so that CsrfViewMiddleware._get_token() works
        token = _get_new_csrf_token()
        self.csrf_client.cookies[settings.CSRF_COOKIE_NAME] = token

        # Post the token matching the cookie value
        response = self.csrf_client.post('/session/', {
            'example': 'example',
            'csrfmiddlewaretoken': token,
        })
        assert response.status_code == status.HTTP_200_OK

    def test_post_form_session_auth_passing(self):
        """
        Ensure POSTing form over session authentication with logged in
        user and CSRF token passes.
        """
        self.non_csrf_client.login(
            username=self.username, password=self.password
        )
        response = self.non_csrf_client.post(
            '/session/', {'example': 'example'}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_put_form_session_auth_passing(self):
        """
        Ensure PUTting form over session authentication with
        logged in user and CSRF token passes.
        """
        self.non_csrf_client.login(
            username=self.username, password=self.password
        )
        response = self.non_csrf_client.put(
            '/session/', {'example': 'example'}
        )
        assert response.status_code == status.HTTP_200_OK

    def test_post_form_session_auth_failing(self):
        """
        Ensure POSTing form over session authentication without logged in user fails.
        """
        response = self.csrf_client.post('/session/', {'example': 'example'})
        assert response.status_code == status.HTTP_403_FORBIDDEN


class BaseTokenAuthTests:
    """Token authentication"""
    model = None
    path = None
    header_prefix = 'Token '

    def setUp(self):
        self.csrf_client = APIClient(enforce_csrf_checks=True)
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            self.username, self.email, self.password
        )

        self.key = 'abcd1234'
        self.token = self.model.objects.create(key=self.key, user=self.user)

    def test_post_form_passing_token_auth(self):
        """
        Ensure POSTing json over token auth with correct
        credentials passes and does not require CSRF
        """
        auth = self.header_prefix + self.key
        response = self.csrf_client.post(
            self.path, {'example': 'example'}, HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_200_OK

    def test_fail_authentication_if_user_is_not_active(self):
        user = User.objects.create_user('foo', 'bar', 'baz')
        user.is_active = False
        user.save()
        self.model.objects.create(key='foobar_token', user=user)
        response = self.csrf_client.post(
            self.path, {'example': 'example'},
            HTTP_AUTHORIZATION=self.header_prefix + 'foobar_token'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_form_passing_nonexistent_token_auth(self):
        # use a nonexistent token key
        auth = self.header_prefix + 'wxyz6789'
        response = self.csrf_client.post(
            self.path, {'example': 'example'}, HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_if_token_is_missing(self):
        response = self.csrf_client.post(
            self.path, {'example': 'example'},
            HTTP_AUTHORIZATION=self.header_prefix)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_if_token_contains_spaces(self):
        response = self.csrf_client.post(
            self.path, {'example': 'example'},
            HTTP_AUTHORIZATION=self.header_prefix + 'foo bar'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_fail_post_form_passing_invalid_token_auth(self):
        # add an 'invalid' unicode character
        auth = self.header_prefix + self.key + "¸"
        response = self.csrf_client.post(
            self.path, {'example': 'example'}, HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_json_passing_token_auth(self):
        """
        Ensure POSTing form over token auth with correct
        credentials passes and does not require CSRF
        """
        auth = self.header_prefix + self.key
        response = self.csrf_client.post(
            self.path, {'example': 'example'},
            format='json', HTTP_AUTHORIZATION=auth
        )
        assert response.status_code == status.HTTP_200_OK

    def test_post_json_makes_one_db_query(self):
        """
        Ensure that authenticating a user using a
        token performs only one DB query
        """
        auth = self.header_prefix + self.key

        def func_to_test():
            return self.csrf_client.post(
                self.path, {'example': 'example'},
                format='json', HTTP_AUTHORIZATION=auth
            )

        self.assertNumQueries(1, func_to_test)

    def test_post_form_failing_token_auth(self):
        """
        Ensure POSTing form over token auth without correct credentials fails
        """
        response = self.csrf_client.post(self.path, {'example': 'example'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_json_failing_token_auth(self):
        """
        Ensure POSTing json over token auth without correct credentials fails
        """
        response = self.csrf_client.post(
            self.path, {'example': 'example'}, format='json'
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@override_settings(ROOT_URLCONF=__name__)
class TokenAuthTests(BaseTokenAuthTests, TestCase):
    model = Token
    path = '/token/'

    def test_token_has_auto_assigned_key_if_none_provided(self):
        """Ensure creating a token with no key will auto-assign a key"""
        self.token.delete()
        token = self.model.objects.create(user=self.user)
        assert bool(token.key)

    def test_generate_key_returns_string(self):
        """Ensure generate_key returns a string"""
        token = self.model()
        key = token.generate_key()
        assert isinstance(key, str)

    def test_generate_key_accessible_as_classmethod(self):
        key = self.model.generate_key()
        assert isinstance(key, str)

    def test_token_login_json(self):
        """Ensure token login view using JSON POST works."""
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            '/auth-token/',
            {'username': self.username, 'password': self.password},
            format='json'
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['token'] == self.key

    def test_token_login_json_bad_creds(self):
        """
        Ensure token login view using JSON POST fails if
        bad credentials are used
        """
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            '/auth-token/',
            {'username': self.username, 'password': "badpass"},
            format='json'
        )
        assert response.status_code == 400

    def test_token_login_json_missing_fields(self):
        """Ensure token login view using JSON POST fails if missing fields."""
        client = APIClient(enforce_csrf_checks=True)
        response = client.post('/auth-token/',
                               {'username': self.username}, format='json')
        assert response.status_code == 400

    def test_token_login_form(self):
        """Ensure token login view using form POST works."""
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            '/auth-token/',
            {'username': self.username, 'password': self.password}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['token'] == self.key


@override_settings(ROOT_URLCONF=__name__)
class CustomTokenAuthTests(BaseTokenAuthTests, TestCase):
    model = CustomToken
    path = '/customtoken/'


@override_settings(ROOT_URLCONF=__name__)
class CustomKeywordTokenAuthTests(BaseTokenAuthTests, TestCase):
    model = Token
    path = '/customkeywordtoken/'
    header_prefix = 'Bearer '


class IncorrectCredentialsTests(TestCase):
    def test_incorrect_credentials(self):
        """
        If a request contains bad authentication credentials, then
        authentication should run and error, even if no permissions
        are set on the view.
        """
        class IncorrectCredentialsAuth(BaseAuthentication):
            def authenticate(self, request):
                raise exceptions.AuthenticationFailed('Bad credentials')

        request = factory.get('/')
        view = MockView.as_view(
            authentication_classes=(IncorrectCredentialsAuth,),
            permission_classes=()
        )
        response = view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {'detail': 'Bad credentials'}


class FailingAuthAccessedInRenderer(TestCase):
    def setUp(self):
        class AuthAccessingRenderer(renderers.BaseRenderer):
            media_type = 'text/plain'
            format = 'txt'

            def render(self, data, media_type=None, renderer_context=None):
                request = renderer_context['request']
                if request.user.is_authenticated:
                    return b'authenticated'
                return b'not authenticated'

        class FailingAuth(BaseAuthentication):
            def authenticate(self, request):
                raise exceptions.AuthenticationFailed('authentication failed')

        class ExampleView(APIView):
            authentication_classes = (FailingAuth,)
            renderer_classes = (AuthAccessingRenderer,)

            def get(self, request):
                return Response({'foo': 'bar'})

        self.view = ExampleView.as_view()

    def test_failing_auth_accessed_in_renderer(self):
        """
        When authentication fails the renderer should still be able to access
        `request.user` without raising an exception. Particularly relevant
        to HTML responses that might reasonably access `request.user`.
        """
        request = factory.get('/')
        response = self.view(request)
        content = response.render().content
        assert content == b'not authenticated'


class NoAuthenticationClassesTests(TestCase):
    def test_permission_message_with_no_authentication_classes(self):
        """
        An unauthenticated request made against a view that contains no
        `authentication_classes` but do contain `permissions_classes` the error
        code returned should be 403 with the exception's message.
        """

        class DummyPermission(permissions.BasePermission):
            message = 'Dummy permission message'

            def has_permission(self, request, view):
                return False

        request = factory.get('/')
        view = MockView.as_view(
            authentication_classes=(),
            permission_classes=(DummyPermission,),
        )
        response = view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data == {'detail': 'Dummy permission message'}


class BasicAuthenticationUnitTests(TestCase):

    def test_base_authentication_abstract_method(self):
        with pytest.raises(NotImplementedError):
            BaseAuthentication().authenticate({})

    def test_basic_authentication_raises_error_if_user_not_found(self):
        auth = BasicAuthentication()
        with pytest.raises(exceptions.AuthenticationFailed):
            auth.authenticate_credentials('invalid id', 'invalid password')

    def test_basic_authentication_raises_error_if_user_not_active(self):
        from rest_framework import authentication

        class MockUser:
            is_active = False
        old_authenticate = authentication.authenticate
        authentication.authenticate = lambda **kwargs: MockUser()
        try:
            auth = authentication.BasicAuthentication()
            with pytest.raises(exceptions.AuthenticationFailed) as exc_info:
                auth.authenticate_credentials('foo', 'bar')
            assert 'User inactive or deleted.' in str(exc_info.value)
        finally:
            authentication.authenticate = old_authenticate


@override_settings(ROOT_URLCONF=__name__,
                   AUTHENTICATION_BACKENDS=('django.contrib.auth.backends.RemoteUserBackend',))
class RemoteUserAuthenticationUnitTests(TestCase):
    def setUp(self):
        self.username = 'john'
        self.email = 'lennon@thebeatles.com'
        self.password = 'password'
        self.user = User.objects.create_user(
            self.username, self.email, self.password
        )

    def test_remote_user_works(self):
        response = self.client.post('/remote-user/',
                                    REMOTE_USER=self.username)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
