from functools import wraps

from django.test import TestCase, override_settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.rest_views import RESTView, get, post, patch
from rest_framework.settings import api_settings


class BasicRESTView(RESTView):

    @get(path='instances/', url_name='instances_list')
    def list(self, request):
        return Response(status=200, data={'http_method': 'GET', 'view_method': 'list'})

    @get(path='instances/<int:instance_id>/', url_name='detail_instance')
    def retrieve(self, request, instance_id: int):
        return Response(status=200, data={'http_method': 'GET', 'view_method': 'retrieve'})

    @post(path='instances/', url_name='instances_list')
    def create(self, request):
        return Response(status=201, data={'http_method': 'POST', 'view_method': 'create'})

    @patch(path='instances/<int:instance_id>/', url_name='detail_instance')
    def update(self, request, instance_id: int):
        return Response(status=200, data={'http_method': 'PATCH', 'view_method': 'update'})

    @patch(path='instances/<int:instance_id>/change/', url_name='detail_instance_change')
    def change_status(self, request, instance_id: int):
        return Response(status=200, data={'http_method': 'PATCH', 'view_method': 'change_status'})


class ErrorRESTView(RESTView):

    @get(path='errors/', url_name='errors_list')
    def error_method(self, request):
        raise Exception


def custom_decorator(view_method):
    @wraps(view_method)
    def wrapper(*args, **kwargs):
        response = view_method(*args, **kwargs)
        response.data['has_decorator'] = True
        return response

    return wrapper


class RESTViewWithCustomDecorators(RESTView):

    @get(path='decorators/', url_name='errors_list')
    @custom_decorator
    def custom_decorator(self, request):
        return Response(status=200, data={'http_method': 'GET', 'view_method': 'custom_decorator'})


urlpatterns = [
    *BasicRESTView.unwrap_url_patterns(),
    *ErrorRESTView.unwrap_url_patterns(),
    *RESTViewWithCustomDecorators.unwrap_url_patterns(),
]


class TestInitializeRESTView(TestCase):

    @staticmethod
    def test_initialize_rest_view():
        assert BasicRESTView._all_actions == {
            'instances/': [
                ('get', 'list', 'instances_list'),
                ('post', 'create', 'instances_list'),
            ],
            'instances/<int:instance_id>/': [
                ('get', 'retrieve', 'detail_instance'),
                ('patch', 'update', 'detail_instance'),
            ],
            'instances/<int:instance_id>/change/': [('patch', 'change_status', 'detail_instance_change')],
        }
        assert not hasattr(BasicRESTView, 'actions')


class TestRESTViewUnwrap(TestCase):

    @staticmethod
    def test_unwrap_url_patterns():
        urlpatterns = BasicRESTView.unwrap_url_patterns()
        assert len(urlpatterns) == 3
        for pattern in urlpatterns:
            assert pattern.callback.cls is not BasicRESTView


@override_settings(ROOT_URLCONF='tests.test_rest_views')
class RESTViewIntegrationTests(TestCase):

    def test_successful_get_request(self):
        response = self.client.get(path='/instances/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'http_method': 'GET', 'view_method': 'list'}

    def test_successful_get_request_with_path_param(self):
        response = self.client.get(path='/instances/1/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'http_method': 'GET', 'view_method': 'retrieve'}

    def test_successful_post_request(self):
        response = self.client.post(path='/instances/')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data == {'http_method': 'POST', 'view_method': 'create'}

    def test_successful_head_request(self):
        response = self.client.head(path='/instances/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'http_method': 'GET', 'view_method': 'list'}

    def test_successful_options_request(self):
        response = self.client.options(path='/instances/')
        assert response.status_code == status.HTTP_200_OK

    def test_method_not_allowed(self):
        response = self.client.put(path='/instances/')
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_method_with_custom_decorator(self):
        response = self.client.get(path='/decorators/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'http_method': 'GET', 'view_method': 'custom_decorator', 'has_decorator': True}


@override_settings(ROOT_URLCONF='tests.test_rest_views')
class TestCustomExceptionHandler(TestCase):

    def setUp(self):
        self.DEFAULT_HANDLER = api_settings.EXCEPTION_HANDLER

        def exception_handler(exc, request):
            return Response('Error!', status=status.HTTP_400_BAD_REQUEST)

        api_settings.EXCEPTION_HANDLER = exception_handler

    def tearDown(self):
        api_settings.EXCEPTION_HANDLER = self.DEFAULT_HANDLER

    def test_class_based_view_exception_handler(self):
        response = self.client.get(path='/errors/')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data == 'Error!'
