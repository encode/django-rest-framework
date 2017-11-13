from django.conf.urls import url
from django.contrib.auth.models import User
from django.test import override_settings

from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from rest_framework.views import APIView

urlpatterns = [
    url(r'^$', APIView.as_view(authentication_classes=(TokenAuthentication,))),
]


class MyMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        assert hasattr(request, 'user'), '`user` is not set on request'
        assert request.user.is_authenticated, '`user` is not authenticated'

        return response


@override_settings(ROOT_URLCONF='tests.test_middleware')
class TestMiddleware(APITestCase):

    @override_settings(MIDDLEWARE=('tests.test_middleware.MyMiddleware',))
    def test_middleware_can_access_user_when_processing_response(self):
        user = User.objects.create_user('john', 'john@example.com', 'password')
        key = 'abcd1234'
        Token.objects.create(key=key, user=user)

        self.client.get('/auth', HTTP_AUTHORIZATION='Token %s' % key)
