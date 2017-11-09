from django.conf.urls import url
from django.test import TestCase, modify_settings, override_settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class MockMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.body
        response = self.get_response(request)
        request.POST
        return response


class MockView(APIView):
    def post(self, request):
        return Response(data=request.data, status=status.HTTP_200_OK)


urlpatterns = [
    url(r'^$', MockView.as_view()),
]


@override_settings(
    ROOT_URLCONF='tests.test_reading_post_directly'
)
@modify_settings(MIDDLEWARE={
    'append': 'tests.test_reading_post_directly.MockMiddleware',
})
class TestReadingPostDirectly(TestCase):
    def test_reading_post_directly(self):
        self.client.post('/', {'foo': 'bar'})
