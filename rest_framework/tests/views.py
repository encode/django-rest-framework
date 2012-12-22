import copy
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.views import APIView

factory = RequestFactory()


class BasicView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'method': 'GET'})

    def post(self, request, *args, **kwargs):
        return Response({'method': 'POST', 'data': request.DATA})


@api_view(['GET', 'POST', 'PUT'])
def basic_view(request):
    if request.method == 'GET':
        return {'method': 'GET'}
    elif request.method == 'POST':
        return {'method': 'POST', 'data': request.DATA}
    elif request.method == 'PUT':
        return {'method': 'PUT', 'data': request.DATA}


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
            'detail': u'JSON parse error - No JSON object could be decoded'
        }
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(sanitise_json_error(response.data), expected)

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
            'detail': u'JSON parse error - No JSON object could be decoded'
        }
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(sanitise_json_error(response.data), expected)


class FunctionBasedViewIntegrationTests(TestCase):
    def setUp(self):
        self.view = basic_view

    def test_400_parse_error(self):
        request = factory.post('/', 'f00bar', content_type='application/json')
        response = self.view(request)
        expected = {
            'detail': u'JSON parse error - No JSON object could be decoded'
        }
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(sanitise_json_error(response.data), expected)

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
            'detail': u'JSON parse error - No JSON object could be decoded'
        }
        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(sanitise_json_error(response.data), expected)
