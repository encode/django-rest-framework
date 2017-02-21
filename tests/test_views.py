from __future__ import unicode_literals

import copy
import sys

from django.test import TestCase

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

factory = APIRequestFactory()

if sys.version_info[:2] >= (3, 4):
    JSON_ERROR = 'JSON parse error - Expecting value:'
else:
    JSON_ERROR = 'JSON parse error - No JSON object could be decoded'


class BasicView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'method': 'GET'})

    def post(self, request, *args, **kwargs):
        return Response({'method': 'POST', 'data': request.data})


@api_view(['GET', 'POST', 'PUT', 'PATCH'])
def basic_view(request):
    if request.method == 'GET':
        return {'method': 'GET'}
    elif request.method == 'POST':
        return {'method': 'POST', 'data': request.data}
    elif request.method == 'PUT':
        return {'method': 'PUT', 'data': request.data}
    elif request.method == 'PATCH':
        return {'method': 'PATCH', 'data': request.data}


class ErrorView(APIView):
    def get(self, request, *args, **kwargs):
        raise Exception


@api_view(['GET'])
def error_view(request):
    raise Exception


def sanitise_json_error(error_dict):
    """
    Exact contents of JSON error messages depend on the installed version
    of json.
    """
    ret = copy.copy(error_dict)
    chop = len(JSON_ERROR)
    ret['detail'] = ret['detail'][:chop]
    return ret


class ClassBasedViewIntegrationTests(TestCase):
    def setUp(self):
        self.view = BasicView.as_view()

    def test_400_parse_error(self):
        request = factory.post('/', 'f00bar', content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': JSON_ERROR
        }
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert sanitise_json_error(response.data) == expected


class FunctionBasedViewIntegrationTests(TestCase):
    def setUp(self):
        self.view = basic_view

    def test_400_parse_error(self):
        request = factory.post('/', 'f00bar', content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': JSON_ERROR
        }
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert sanitise_json_error(response.data) == expected


class TestCustomExceptionHandler(TestCase):
    def setUp(self):
        self.DEFAULT_HANDLER = api_settings.EXCEPTION_HANDLER

        def exception_handler(exc, request):
            return Response('Error!', status=status.HTTP_400_BAD_REQUEST)

        api_settings.EXCEPTION_HANDLER = exception_handler

    def tearDown(self):
        api_settings.EXCEPTION_HANDLER = self.DEFAULT_HANDLER

    def test_class_based_view_exception_handler(self):
        view = ErrorView.as_view()

        request = factory.get('/', content_type='application/json')
        response = view(request)
        expected = 'Error!'
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == expected

    def test_function_based_view_exception_handler(self):
        view = error_view

        request = factory.get('/', content_type='application/json')
        response = view(request)
        expected = 'Error!'
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == expected
