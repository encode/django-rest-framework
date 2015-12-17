from django.test import TestCase

from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

factory = APIRequestFactory()


class ExampleSerializer(serializers.Serializer):
    char = serializers.CharField()
    integer = serializers.IntegerField()


class ErrorView(APIView):
    def get(self, request, *args, **kwargs):
        ExampleSerializer(data={}).is_valid(raise_exception=True)


@api_view(['GET'])
def error_view(request):
    ExampleSerializer(data={}).is_valid(raise_exception=True)


class TestValidationErrorWithCode(TestCase):
    def setUp(self):
        self.DEFAULT_HANDLER = api_settings.EXCEPTION_HANDLER

        def exception_handler(exc, request):
            return_errors = {}
            for field_name, errors in exc.detail.items():
                return_errors[field_name] = []
                for error in errors:
                    return_errors[field_name].append({
                        'code': error.code,
                        'message': error
                    })

            return Response(return_errors, status=status.HTTP_400_BAD_REQUEST)

        api_settings.EXCEPTION_HANDLER = exception_handler

        self.expected_response_data = {
            'char': [{
                'message': 'This field is required.',
                'code': 'required',
            }],
            'integer': [{
                'message': 'This field is required.',
                'code': 'required'
            }],
        }

    def tearDown(self):
        api_settings.EXCEPTION_HANDLER = self.DEFAULT_HANDLER

    def test_class_based_view_exception_handler(self):
        view = ErrorView.as_view()

        request = factory.get('/', content_type='application/json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, self.expected_response_data)

    def test_function_based_view_exception_handler(self):
        view = error_view

        request = factory.get('/', content_type='application/json')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, self.expected_response_data)
