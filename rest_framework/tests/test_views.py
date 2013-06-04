from __future__ import unicode_literals

import copy
import warnings

from django.test import TestCase
from django.test.client import RequestFactory

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView
from rest_framework.exceptions import ParseError

factory = RequestFactory()


class BasicView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'method': 'GET'})

    def post(self, request, *args, **kwargs):
        if 'raise_400_error' in request.DATA:
            raise ParseError('Bad request')
        if 'return_400_error' in request.DATA:
            return Response({'detail': 'Bad request'},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response({'method': 'POST', 'data': request.DATA})


@api_view(['GET', 'POST', 'PUT', 'PATCH'])
def basic_view(request):
    if request.method == 'GET':
        return {'method': 'GET'}
    if request.method in ('POST', 'PUT', 'PATCH'):
        if 'raise_400_error' in request.DATA:
            raise ParseError('Bad request')
        if 'return_400_error' in request.DATA:
            return Response({'detail': 'Bad request'},
                            status=status.HTTP_400_BAD_REQUEST)
        return {'method': request.method, 'data': request.DATA}


def sanitise_json_error(error_dict):
    """
    Exact contents of JSON error messages depend on the installed version
    of json.
    """
    ret = copy.copy(error_dict)
    chop = len('JSON parse error - No JSON object could be decoded')
    ret['detail'] = ret['detail'][:chop]
    return ret


class ClassBasedViewIntegrationTests(TestCase):
    def setUp(self):
        self.view = BasicView.as_view()

    def test_400_parse_error(self):
        request = factory.post('/', 'f00bar', content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': 'JSON parse error - No JSON object could be decoded'
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_400_parse_error_tunneled_content(self):
        content = 'f00bar'
        content_type = 'application/json'
        form_data = {
            api_settings.FORM_CONTENT_OVERRIDE: content,
            api_settings.FORM_CONTENTTYPE_OVERRIDE: content_type
        }
        request = factory.post('/', form_data)
        response = self.view(request)
        expected = {
            'detail': 'JSON parse error - No JSON object could be decoded'
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_raise_400_error(self):
        request = factory.post('/', '{"raise_400_error": true}',
                               content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': 'Bad request'
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_return_400_error(self):
        request = factory.post('/', '{"return_400_error": true}',
                               content_type='application/json')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            response = self.view(request)
            self.assertEqual(len(w), 1)
        expected = {
            'detail': 'Bad request'
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
            'detail': 'JSON parse error - No JSON object could be decoded'
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_400_parse_error_tunneled_content(self):
        content = 'f00bar'
        content_type = 'application/json'
        form_data = {
            api_settings.FORM_CONTENT_OVERRIDE: content,
            api_settings.FORM_CONTENTTYPE_OVERRIDE: content_type
        }
        request = factory.post('/', form_data)
        response = self.view(request)
        expected = {
            'detail': 'JSON parse error - No JSON object could be decoded'
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_raise_400_error(self):
        request = factory.post('/', '{"raise_400_error": true}',
                               content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': 'Bad request'
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)

    def test_return_400_error(self):
        request = factory.post('/', '{"return_400_error": true}',
                               content_type='application/json')
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            response = self.view(request)
            self.assertEqual(len(w), 1)
        expected = {
            'detail': 'Bad request'
        }
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(sanitise_json_error(response.data), expected)
