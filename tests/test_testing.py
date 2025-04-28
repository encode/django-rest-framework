import itertools
from io import BytesIO
from unittest.mock import patch

from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.test import TestCase, override_settings
from django.urls import path

from rest_framework import fields, parsers, renderers, serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    api_view, parser_classes, renderer_classes
)
from rest_framework.response import Response
from rest_framework.test import (
    APIClient, APIRequestFactory, URLPatternsTestCase, force_authenticate
)


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
def view(request):
    data = {'auth': request.META.get('HTTP_AUTHORIZATION', b'')}
    if request.user:
        data['user'] = request.user.username
    if request.auth:
        data['token'] = request.auth.key
    return Response(data)


@api_view(['GET', 'POST'])
def session_view(request):
    active_session = request.session.get('active_session', False)
    request.session['active_session'] = True
    return Response({
        'active_session': active_session
    })


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
def redirect_view(request):
    return redirect('/view/')


@api_view(['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
def redirect_307_308_view(request, code):
    return HttpResponseRedirect('/view/', status=code)


class BasicSerializer(serializers.Serializer):
    flag = fields.BooleanField(default=lambda: True)


@api_view(['POST'])
@parser_classes((parsers.JSONParser,))
def post_json_view(request):
    return Response(request.data)


@api_view(['DELETE'])
@renderer_classes((renderers.JSONRenderer, ))
def delete_json_view(request):
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def post_view(request):
    serializer = BasicSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    return Response(serializer.validated_data)


urlpatterns = [
    path('view/', view),
    path('session-view/', session_view),
    path('redirect-view/', redirect_view),
    path('redirect-view/<int:code>/', redirect_307_308_view),
    path('post-json-view/', post_json_view),
    path('delete-json-view/', delete_json_view),
    path('post-view/', post_view),
]


@override_settings(ROOT_URLCONF='tests.test_testing')
class TestAPITestClient(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_credentials(self):
        """
        Setting `.credentials()` adds the required headers to each request.
        """
        self.client.credentials(HTTP_AUTHORIZATION='example')
        for _ in range(0, 3):
            response = self.client.get('/view/')
            assert response.data['auth'] == 'example'

    def test_force_authenticate_with_user(self):
        """
        Setting `.force_authenticate()` with a user forcibly authenticates each
        request with that user.
        """
        user = User.objects.create_user('example', 'example@example.com')

        self.client.force_authenticate(user=user)
        response = self.client.get('/view/')

        assert response.data['user'] == 'example'
        assert 'token' not in response.data

    def test_force_authenticate_with_token(self):
        """
        Setting `.force_authenticate()` with a token forcibly authenticates each
        request with that token.
        """
        user = User.objects.create_user('example', 'example@example.com')
        token = Token.objects.create(key='xyz', user=user)

        self.client.force_authenticate(token=token)
        response = self.client.get('/view/')

        assert response.data['token'] == 'xyz'
        assert 'user' not in response.data

    def test_force_authenticate_with_user_and_token(self):
        """
        Setting `.force_authenticate()` with a user and token forcibly
        authenticates each request with that user and token.
        """
        user = User.objects.create_user('example', 'example@example.com')
        token = Token.objects.create(key='xyz', user=user)

        self.client.force_authenticate(user=user, token=token)
        response = self.client.get('/view/')

        assert response.data['user'] == 'example'
        assert response.data['token'] == 'xyz'

    def test_force_authenticate_with_sessions(self):
        """
        Setting `.force_authenticate()` forcibly authenticates each request.
        """
        user = User.objects.create_user('example', 'example@example.com')
        self.client.force_authenticate(user)

        # First request does not yet have an active session
        response = self.client.get('/session-view/')
        assert response.data['active_session'] is False

        # Subsequent requests have an active session
        response = self.client.get('/session-view/')
        assert response.data['active_session'] is True

        # Force authenticating with `None` user and token should also logout
        # the user session.
        self.client.force_authenticate(user=None, token=None)
        response = self.client.get('/session-view/')
        assert response.data['active_session'] is False

    def test_csrf_exempt_by_default(self):
        """
        By default, the test client is CSRF exempt.
        """
        User.objects.create_user('example', 'example@example.com', 'password')
        self.client.login(username='example', password='password')
        response = self.client.post('/view/')
        assert response.status_code == 200

    def test_explicitly_enforce_csrf_checks(self):
        """
        The test client can enforce CSRF checks.
        """
        client = APIClient(enforce_csrf_checks=True)
        User.objects.create_user('example', 'example@example.com', 'password')
        client.login(username='example', password='password')
        response = client.post('/view/')
        expected = {'detail': 'CSRF Failed: CSRF cookie not set.'}
        assert response.status_code == 403
        assert response.data == expected

    def test_can_logout(self):
        """
        `logout()` resets stored credentials
        """
        self.client.credentials(HTTP_AUTHORIZATION='example')
        response = self.client.get('/view/')
        assert response.data['auth'] == 'example'
        self.client.logout()
        response = self.client.get('/view/')
        assert response.data['auth'] == b''

    def test_logout_resets_force_authenticate(self):
        """
        `logout()` resets any `force_authenticate`
        """
        user = User.objects.create_user('example', 'example@example.com', 'password')
        self.client.force_authenticate(user)
        response = self.client.get('/view/')
        assert response.data['user'] == 'example'
        self.client.logout()
        response = self.client.get('/view/')
        assert response.data['user'] == ''

    def test_follow_redirect(self):
        """
        Follow redirect by setting follow argument.
        """
        for method in ('get', 'post', 'put', 'patch', 'delete', 'options'):
            with self.subTest(method=method):
                req_method = getattr(self.client, method)
                response = req_method('/redirect-view/')
                assert response.status_code == 302
                response = req_method('/redirect-view/', follow=True)
                assert response.redirect_chain is not None
                assert response.status_code == 200

    def test_follow_307_308_preserve_kwargs(self, *mocked_methods):
        """
        Follow redirect by setting follow argument, and make sure the following
        method called with appropriate kwargs.
        """
        methods = ('get', 'post', 'put', 'patch', 'delete', 'options')
        codes = (307, 308)
        for method, code in itertools.product(methods, codes):
            subtest_ctx = self.subTest(method=method, code=code)
            patch_ctx = patch.object(self.client, method, side_effect=getattr(self.client, method))
            with subtest_ctx, patch_ctx as req_method:
                kwargs = {'data': {'example': 'test'}, 'format': 'json'}
                response = req_method('/redirect-view/%s/' % code, follow=True, **kwargs)
                assert response.redirect_chain is not None
                assert response.status_code == 200
                for _, call_args, call_kwargs in req_method.mock_calls:
                    assert all(call_kwargs[k] == kwargs[k] for k in kwargs if k in call_kwargs)

    def test_invalid_multipart_data(self):
        """
        MultiPart encoding cannot support nested data, so raise a helpful
        error if the user attempts to do so.
        """
        self.assertRaises(
            AssertionError, self.client.post,
            path='/view/', data={'valid': 123, 'invalid': {'a': 123}}
        )

    def test_empty_post_uses_default_boolean_value(self):
        response = self.client.post(
            '/post-view/',
            data=None,
            content_type='application/json'
        )
        assert response.status_code == 200
        assert response.data == {"flag": True}

    def test_post_encodes_data_based_on_json_content_type(self):
        data = {'data': True}
        response = self.client.post(
            '/post-json-view/',
            data=data,
            content_type='application/json'
        )

        assert response.status_code == 200
        assert response.data == data

    def test_delete_based_on_format(self):
        response = self.client.delete('/delete-json-view/', format='json')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert response.data is None


class TestAPIRequestFactory(TestCase):
    def test_csrf_exempt_by_default(self):
        """
        By default, the test client is CSRF exempt.
        """
        user = User.objects.create_user('example', 'example@example.com', 'password')
        factory = APIRequestFactory()
        request = factory.post('/view/')
        request.user = user
        response = view(request)
        assert response.status_code == 200

    def test_explicitly_enforce_csrf_checks(self):
        """
        The test client can enforce CSRF checks.
        """
        user = User.objects.create_user('example', 'example@example.com', 'password')
        factory = APIRequestFactory(enforce_csrf_checks=True)
        request = factory.post('/view/')
        request.user = user
        response = view(request)
        expected = {'detail': 'CSRF Failed: CSRF cookie not set.'}
        assert response.status_code == 403
        assert response.data == expected

    def test_invalid_format(self):
        """
        Attempting to use a format that is not configured will raise an
        assertion error.
        """
        factory = APIRequestFactory()
        self.assertRaises(
            AssertionError, factory.post,
            path='/view/', data={'example': 1}, format='xml'
        )

    def test_force_authenticate(self):
        """
        Setting `force_authenticate()` forcibly authenticates the request.
        """
        user = User.objects.create_user('example', 'example@example.com')
        factory = APIRequestFactory()
        request = factory.get('/view')
        force_authenticate(request, user=user)
        response = view(request)
        assert response.data['user'] == 'example'

    def test_upload_file(self):
        # This is a 1x1 black png
        simple_png = BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc````\x00\x00\x00\x05\x00\x01\xa5\xf6E@\x00\x00\x00\x00IEND\xaeB`\x82')
        simple_png.name = 'test.png'
        factory = APIRequestFactory()
        factory.post('/', data={'image': simple_png})

    def test_request_factory_url_arguments(self):
        """
        This is a non regression test against #1461
        """
        factory = APIRequestFactory()
        request = factory.get('/view/?demo=test')
        assert dict(request.GET) == {'demo': ['test']}
        request = factory.get('/view/', {'demo': 'test'})
        assert dict(request.GET) == {'demo': ['test']}

    def test_request_factory_url_arguments_with_unicode(self):
        factory = APIRequestFactory()
        request = factory.get('/view/?demo=testé')
        assert dict(request.GET) == {'demo': ['testé']}
        request = factory.get('/view/', {'demo': 'testé'})
        assert dict(request.GET) == {'demo': ['testé']}

    def test_empty_request_content_type(self):
        factory = APIRequestFactory()
        request = factory.post(
            '/post-view/',
            data=None,
            content_type='application/json',
        )
        assert request.META['CONTENT_TYPE'] == 'application/json'


class TestUrlPatternTestCase(URLPatternsTestCase):
    urlpatterns = [
        path('', view),
    ]

    @classmethod
    def setUpClass(cls):
        assert urlpatterns is not cls.urlpatterns
        super().setUpClass()
        assert urlpatterns is cls.urlpatterns

    @classmethod
    def doClassCleanups(cls):
        assert urlpatterns is cls.urlpatterns
        super().doClassCleanups()
        assert urlpatterns is not cls.urlpatterns

    def test_urlpatterns(self):
        assert self.client.get('/').status_code == 200


class TestExistingPatterns(TestCase):
    def test_urlpatterns(self):
        # sanity test to ensure that this test module does not have a '/' route
        assert self.client.get('/').status_code == 404
