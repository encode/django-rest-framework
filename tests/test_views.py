import copy
import re

from django.test import TestCase

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.settings import APISettings, api_settings
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

factory = APIRequestFactory()

JSON_ERROR = 'JSON parse error - Expecting value:'
STATUS_CODE_400 = 'Bad Request'
REASON_PHRASE_RE = r"{} \({}.*\)".format(STATUS_CODE_400, JSON_ERROR)
VALIDATION_ERROR = "Data isn't valid!"


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


class ValidationErrorView(APIView):
    def get(self, request, *args, **kwargs):
        raise ValidationError(VALIDATION_ERROR)


def custom_handler(exc, context):
    if isinstance(exc, SyntaxError):
        return Response({'error': 'SyntaxError'}, status=400)
    return Response({'error': 'UnknownError'}, status=500)


class OverridenSettingsView(APIView):
    settings = APISettings({'EXCEPTION_HANDLER': custom_handler})

    def get(self, request, *args, **kwargs):
        raise SyntaxError('request is invalid syntax')


@api_view(['GET'])
def error_view(request):
    raise Exception


@api_view(['GET'])
def validation_error_view(request):
    raise ValidationError(VALIDATION_ERROR)


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

    def test_400_parse_error(self):
        request = factory.post('/', 'f00bar', content_type='application/json')
        response = BasicView.as_view()(request)
        expected = {
            'detail': JSON_ERROR
        }
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert re.match(REASON_PHRASE_RE, response.reason_phrase)
        assert sanitise_json_error(response.data) == expected

    def test_400_validation_error(self):
        request = factory.get('/')
        response = ValidationErrorView.as_view()(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.reason_phrase == "{} ({})".format(STATUS_CODE_400, VALIDATION_ERROR)
        assert response.data == [VALIDATION_ERROR]


class FunctionBasedViewIntegrationTests(TestCase):

    def test_400_parse_error(self):
        request = factory.post('/', 'f00bar', content_type='application/json')
        response = basic_view(request)
        expected = {
            'detail': JSON_ERROR
        }
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert re.match(REASON_PHRASE_RE, response.reason_phrase)
        assert sanitise_json_error(response.data) == expected

    def test_400_validation_error(self):
        request = factory.get('/')
        response = validation_error_view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.reason_phrase == "{} ({})".format(STATUS_CODE_400, VALIDATION_ERROR)
        assert response.data == [VALIDATION_ERROR]


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


class TestCustomSettings(TestCase):
    def setUp(self):
        self.view = OverridenSettingsView.as_view()

    def test_get_exception_handler(self):
        request = factory.get('/', content_type='application/json')
        response = self.view(request)
        assert response.status_code == 400
        assert response.data == {'error': 'SyntaxError'}
