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


class TestValidationErrorWithFullDetails(TestCase):
    def setUp(self):
        self.DEFAULT_HANDLER = api_settings.EXCEPTION_HANDLER

        def exception_handler(exc, request):
            data = exc.get_full_details()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

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
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == self.expected_response_data

    def test_function_based_view_exception_handler(self):
        view = error_view

        request = factory.get('/', content_type='application/json')
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == self.expected_response_data


class TestValidationErrorWithCodes(TestCase):
    def setUp(self):
        self.DEFAULT_HANDLER = api_settings.EXCEPTION_HANDLER

        def exception_handler(exc, request):
            data = exc.get_codes()
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        api_settings.EXCEPTION_HANDLER = exception_handler

        self.expected_response_data = {
            'char': ['required'],
            'integer': ['required'],
        }

    def tearDown(self):
        api_settings.EXCEPTION_HANDLER = self.DEFAULT_HANDLER

    def test_class_based_view_exception_handler(self):
        view = ErrorView.as_view()

        request = factory.get('/', content_type='application/json')
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == self.expected_response_data

    def test_function_based_view_exception_handler(self):
        view = error_view

        request = factory.get('/', content_type='application/json')
        response = view(request)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == self.expected_response_data


class TestValidationErrorConvertsTuplesToLists(TestCase):
    def test_validation_error_details(self):
        error = ValidationError(detail=('message1', 'message2'))
        assert isinstance(error.detail, list)
        assert len(error.detail) == 2
        assert str(error.detail[0]) == 'message1'
        assert str(error.detail[1]) == 'message2'


class TestValidationErrorWithDjangoStyle(TestCase):
    def test_validation_error_details(self):
        error = ValidationError('Invalid value: %(value)s', params={'value': '42'})
        assert str(error.detail[0]) == 'Invalid value: 42'

    def test_validation_error_details_tuple(self):
        error = ValidationError(
            detail=('Invalid value: %(value1)s', 'Invalid value: %(value2)s'),
            params={'value1': '42', 'value2': '43'},
        )
        assert isinstance(error.detail, list)
        assert len(error.detail) == 2
        assert str(error.detail[0]) == 'Invalid value: 42'
        assert str(error.detail[1]) == 'Invalid value: 43'

    def test_validation_error_details_list(self):
        error = ValidationError(
            detail=['Invalid value: %(value1)s', 'Invalid value: %(value2)s', ],
            params={'value1': '42', 'value2': '43'}
        )
        assert isinstance(error.detail, list)
        assert len(error.detail) == 2
        assert str(error.detail[0]) == 'Invalid value: 42'
        assert str(error.detail[1]) == 'Invalid value: 43'

    def test_validation_error_details_validation_errors(self):
        error = ValidationError(
            detail=ValidationError(
                detail='Invalid value: %(value1)s',
                params={'value1': '42'},
            ),
        )
        assert isinstance(error.detail, list)
        assert len(error.detail) == 1
        assert str(error.detail[0]) == 'Invalid value: 42'

    def test_validation_error_details_validation_errors_list(self):
        error = ValidationError(
            detail=[
                ValidationError(
                    detail='Invalid value: %(value1)s',
                    params={'value1': '42'},
                ),
                ValidationError(
                    detail='Invalid value: %(value2)s',
                    params={'value2': '43'},
                ),
                'Invalid value: %(value3)s'
            ],
            params={'value3': '44'}
        )
        assert isinstance(error.detail, list)
        assert len(error.detail) == 3
        assert str(error.detail[0]) == 'Invalid value: 42'
        assert str(error.detail[1]) == 'Invalid value: 43'
        assert str(error.detail[2]) == 'Invalid value: 44'

    def test_validation_error_details_validation_errors_nested_list(self):
        error = ValidationError(
            detail=[
                ValidationError(
                    detail='Invalid value: %(value1)s',
                    params={'value1': '42'},
                ),
                ValidationError(
                    detail=[
                        'Invalid value: %(value2)s',
                        ValidationError(
                            detail='Invalid value: %(value3)s',
                            params={'value3': '44'},
                        )
                    ],
                    params={'value2': '43'},
                ),
                'Invalid value: %(value4)s'
            ],
            params={'value4': '45'}
        )
        assert isinstance(error.detail, list)
        assert len(error.detail) == 4
        assert str(error.detail[0]) == 'Invalid value: 42'
        assert str(error.detail[1]) == 'Invalid value: 43'
        assert str(error.detail[2]) == 'Invalid value: 44'
        assert str(error.detail[3]) == 'Invalid value: 45'
