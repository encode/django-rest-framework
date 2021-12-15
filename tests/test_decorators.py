import pytest
from django.test import TestCase

from rest_framework import status
from rest_framework.authentication import BasicAuthentication
from rest_framework.decorators import (
    action, api_view, authentication_classes, parser_classes,
    permission_classes, renderer_classes, schema, throttle_classes
)
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from rest_framework.test import APIRequestFactory
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView


class DecoratorTestCase(TestCase):

    def setUp(self):
        self.factory = APIRequestFactory()

    def test_api_view_incorrect(self):
        """
        If @api_view is not applied correct, we should raise an assertion.
        """

        @api_view
        def view(request):
            return Response()

        request = self.factory.get('/')
        self.assertRaises(AssertionError, view, request)

    def test_api_view_incorrect_arguments(self):
        """
        If @api_view is missing arguments, we should raise an assertion.
        """

        with self.assertRaises(AssertionError):
            @api_view('GET')
            def view(request):
                return Response()

    def test_calling_method(self):

        @api_view(['GET'])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        request = self.factory.post('/')
        response = view(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_calling_put_method(self):

        @api_view(['GET', 'PUT'])
        def view(request):
            return Response({})

        request = self.factory.put('/')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        request = self.factory.post('/')
        response = view(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_calling_patch_method(self):

        @api_view(['GET', 'PATCH'])
        def view(request):
            return Response({})

        request = self.factory.patch('/')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        request = self.factory.post('/')
        response = view(request)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_renderer_classes(self):

        @api_view(['GET'])
        @renderer_classes([JSONRenderer])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        assert isinstance(response.accepted_renderer, JSONRenderer)

    def test_parser_classes(self):

        @api_view(['GET'])
        @parser_classes([JSONParser])
        def view(request):
            assert len(request.parsers) == 1
            assert isinstance(request.parsers[0], JSONParser)
            return Response({})

        request = self.factory.get('/')
        view(request)

    def test_authentication_classes(self):

        @api_view(['GET'])
        @authentication_classes([BasicAuthentication])
        def view(request):
            assert len(request.authenticators) == 1
            assert isinstance(request.authenticators[0], BasicAuthentication)
            return Response({})

        request = self.factory.get('/')
        view(request)

    def test_permission_classes(self):

        @api_view(['GET'])
        @permission_classes([IsAuthenticated])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_throttle_classes(self):
        class OncePerDayUserThrottle(UserRateThrottle):
            rate = '1/day'

        @api_view(['GET'])
        @throttle_classes([OncePerDayUserThrottle])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

        response = view(request)
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_schema(self):
        """
        Checks CustomSchema class is set on view
        """
        class CustomSchema(AutoSchema):
            pass

        @api_view(['GET'])
        @schema(CustomSchema())
        def view(request):
            return Response({})

        assert isinstance(view.cls.schema, CustomSchema)


class ActionDecoratorTestCase(TestCase):

    def test_defaults(self):
        @action(detail=True)
        def test_action(request):
            """Description"""

        assert test_action.mapping == {'get': 'test_action'}
        assert test_action.detail is True
        assert test_action.url_path == 'test_action'
        assert test_action.url_name == 'test-action'
        assert test_action.kwargs == {
            'name': 'Test action',
            'description': 'Description',
        }

    def test_detail_required(self):
        with pytest.raises(AssertionError) as excinfo:
            @action()
            def test_action(request):
                raise NotImplementedError

        assert str(excinfo.value) == "@action() missing required argument: 'detail'"

    def test_method_mapping_http_methods(self):
        # All HTTP methods should be mappable
        @action(detail=False, methods=[])
        def test_action():
            raise NotImplementedError

        for name in APIView.http_method_names:
            def method():
                raise NotImplementedError

            method.__name__ = name
            getattr(test_action.mapping, name)(method)

        # ensure the mapping returns the correct method name
        for name in APIView.http_method_names:
            assert test_action.mapping[name] == name

    def test_view_name_kwargs(self):
        """
        'name' and 'suffix' are mutually exclusive kwargs used for generating
        a view's display name.
        """
        # by default, generate name from method
        @action(detail=True)
        def test_action(request):
            raise NotImplementedError

        assert test_action.kwargs == {
            'description': None,
            'name': 'Test action',
        }

        # name kwarg supersedes name generation
        @action(detail=True, name='test name')
        def test_action(request):
            raise NotImplementedError

        assert test_action.kwargs == {
            'description': None,
            'name': 'test name',
        }

        # suffix kwarg supersedes name generation
        @action(detail=True, suffix='Suffix')
        def test_action(request):
            raise NotImplementedError

        assert test_action.kwargs == {
            'description': None,
            'suffix': 'Suffix',
        }

        # name + suffix is a conflict.
        with pytest.raises(TypeError) as excinfo:
            action(detail=True, name='test name', suffix='Suffix')

        assert str(excinfo.value) == "`name` and `suffix` are mutually exclusive arguments."

    def test_method_mapping(self):
        @action(detail=False)
        def test_action(request):
            raise NotImplementedError

        @test_action.mapping.post
        def test_action_post(request):
            raise NotImplementedError

        # The secondary handler methods should not have the action attributes
        for name in ['mapping', 'detail', 'url_path', 'url_name', 'kwargs']:
            assert hasattr(test_action, name) and not hasattr(test_action_post, name)

    def test_method_mapping_already_mapped(self):
        @action(detail=True)
        def test_action(request):
            raise NotImplementedError

        msg = "Method 'get' has already been mapped to '.test_action'."
        with self.assertRaisesMessage(AssertionError, msg):
            @test_action.mapping.get
            def test_action_get(request):
                raise NotImplementedError

    def test_method_mapping_overwrite(self):
        @action(detail=True)
        def test_action():
            raise NotImplementedError

        msg = ("Method mapping does not behave like the property decorator. You "
               "cannot use the same method name for each mapping declaration.")
        with self.assertRaisesMessage(AssertionError, msg):
            @test_action.mapping.post
            def test_action():
                raise NotImplementedError
