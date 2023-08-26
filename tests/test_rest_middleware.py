from django.test import TestCase, override_settings
from django.urls import path

from rest_framework import status
from rest_framework.middleware import (
    BarMiddleware, BaseMiddleware, FooMiddleware
)
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

factory = APIRequestFactory()


class DummyRequestMiddleware(BaseMiddleware):
    def process_request(self, request):
        request._dummy = "dummy"


class DummyResponseMiddleware(BarMiddleware):
    def process_response(self, response):
        response._dummy = "dummy"


class MockView(APIView):
    def get(self, request):
        response = Response(status=status.HTTP_200_OK)
        response._request = request  # test client sets `request` input
        return response


urlpatterns = [
    path('foo/', MockView.as_view(middleware_classes=[FooMiddleware])),
    path('bar/', MockView.as_view(middleware_classes=[BarMiddleware])),
    path('multiple/', MockView.as_view(middleware_classes=[DummyRequestMiddleware, DummyResponseMiddleware])),
    path('none/', MockView.as_view(middleware_classes=[]))
]


@override_settings(ROOT_URLCONF=__name__)
class FooMiddlewareTests(TestCase):
    def test_foo_middleware_process_request(self):
        response = APIClient().get('/foo/')
        request = response._request
        assert getattr(request, "_foo") == "foo"
        assert response.status_code == status.HTTP_200_OK


@override_settings(ROOT_URLCONF=__name__)
class BarMiddlewareTests(TestCase):
    def test_bar_middleware_process_response(self):
        response = APIClient().get('/bar/')
        assert getattr(response, "_bar") == "bar"
        assert response.status_code == status.HTTP_200_OK


@override_settings(ROOT_URLCONF=__name__)
class MultipleMiddlewareClassesTests(TestCase):
    def test_multiple_middleware_classes_process_request_and_response(self):
        response = APIClient().get('/multiple/')
        request = response._request
        assert getattr(request, "_dummy") == "dummy"
        assert getattr(response, "_dummy") == "dummy"
        assert response.status_code == status.HTTP_200_OK


@override_settings(ROOT_URLCONF=__name__)
class NoMiddlewareClassesTests(TestCase):
    def test_no_middleware_classes(self):
        response = APIClient().get('/none/')
        assert response.status_code == status.HTTP_200_OK
