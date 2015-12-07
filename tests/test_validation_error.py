import pytest
from django.test import TestCase

from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
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
            if not exc.code:
                errors = {
                    field_name: {
                        'code': e.code,
                        'message': e.detail
                    } for field_name, e in exc.detail.items()
                }
            else:
                errors = {
                    'code': exc.code,
                    'detail': exc.detail
                }
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        api_settings.EXCEPTION_HANDLER = exception_handler

        self.expected_response_data = {
            'char': {
                'message': ['This field is required.'],
                'code': 'required',
            },
            'integer': {
                'message': ['This field is required.'],
                'code': 'required'
            },
        }

    def tearDown(self):
        api_settings.EXCEPTION_HANDLER = self.DEFAULT_HANDLER

    def test_validation_error_requires_no_code_for_structured_errors(self):
        """
        ValidationError can hold a list or dictionary of simple errors, in
        which case the code is no longer meaningful and should not be
        specified.
        """
        with pytest.raises(AssertionError):
            serializers.ValidationError([ValidationError("test-detail", "test-code")], code='min_value')

        with pytest.raises(AssertionError):
            serializers.ValidationError({}, code='min_value')

    def test_validation_error_stores_error_code(self):
        exception = serializers.ValidationError("", code='min_value')
        assert exception.code == 'min_value'

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
