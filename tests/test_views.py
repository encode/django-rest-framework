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
from rest_framework.exceptions import PermissionDenied
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied

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


@api_view(['GET'])
def permissiondenied_instance_view(request):
    return PermissionDenied()
    raise PermissionDenied()

@api_view(['GET'])
def permissiondenied_class_view(request):
    raise PermissionDenied

@api_view(['GET'])
def django_permissiondenied_instance_view(request):
    raise DjangoPermissionDenied()

@api_view(['GET'])
def django_permissiondenied_class_view(request):
    raise DjangoPermissionDenied



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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)


class FunctionBasedViewIntegrationTests(TestCase):
    def setUp(self):
        self.view = basic_view

    def test_400_parse_error(self):
        request = factory.post('/', 'f00bar', content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': JSON_ERROR
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)


class FuncionBasedPermissionDeniedTests(TestCase):


    def setUp(self):
        self.authentication_classes = api_settings.DEFAULT_AUTHENTICATION_CLASSES
        api_settings.DEFAULT_AUTHENTICATION_CLASSES = 'rest_framework.permissions.IsAuthenticated'

    def tearDown(self):
         api_settings.DEFAULT_AUTHENTICATION_CLASSES = self.authentication_classes

    def test_permission_denied_instance_error(self):
        self.view = permissiondenied_instance_view
        request = factory.get('/', content_type='application/json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        expected = {
            'detail': 'You do not have permission to perform this action.'
        }
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_permission_denied_class_error(self):
        self.view = permissiondenied_class_view

        request = factory.get('/', content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': 'You do not have permission to perform this action.'
        }
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_django_permission_denied_instance_error(self):
        self.view = django_permissiondenied_instance_view
        request = factory.get('/', content_type='application/json')
        response = self.view(request)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        expected = {
            'detail': u'Permission denied.'
        }
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_django_permission_denied_class_error(self):
        self.view = django_permissiondenied_class_view
        request = factory.get('/', content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': u'Permission denied.'
        }
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(sanitise_json_error(response.data), expected)



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
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected)

    def test_function_based_view_exception_handler(self):
        view = error_view

        request = factory.get('/', content_type='application/json')
        response = view(request)
        expected = 'Error!'
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected)
