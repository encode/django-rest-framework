from __future__ import unicode_literals
from django.test import TestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.authentication import BasicAuthentication
from rest_framework.throttling import UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.decorators import (
    api_view,
    renderer_classes,
    parser_classes,
    authentication_classes,
    throttle_classes,
    permission_classes,
)

from rest_framework.tests.utils import RequestFactory


class DecoratorTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def _finalize_response(self, request, response, *args, **kwargs):
        response.request = request
        return APIView.finalize_response(self, request, response, *args, **kwargs)

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
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request = self.factory.post('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_calling_put_method(self):

        @api_view(['GET', 'PUT'])
        def view(request):
            return Response({})

        request = self.factory.put('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request = self.factory.post('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_calling_patch_method(self):

        @api_view(['GET', 'PATCH'])
        def view(request):
            return Response({})

        request = self.factory.patch('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        request = self.factory.post('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_renderer_classes(self):

        @api_view(['GET'])
        @renderer_classes([JSONRenderer])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        self.assertTrue(isinstance(response.accepted_renderer, JSONRenderer))

    def test_parser_classes(self):

        @api_view(['GET'])
        @parser_classes([JSONParser])
        def view(request):
            self.assertEqual(len(request.parsers), 1)
            self.assertTrue(isinstance(request.parsers[0],
                                       JSONParser))
            return Response({})

        request = self.factory.get('/')
        view(request)

    def test_authentication_classes(self):

        @api_view(['GET'])
        @authentication_classes([BasicAuthentication])
        def view(request):
            self.assertEqual(len(request.authenticators), 1)
            self.assertTrue(isinstance(request.authenticators[0],
                                       BasicAuthentication))
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
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_throttle_classes(self):
        class OncePerDayUserThrottle(UserRateThrottle):
            rate = '1/day'

        @api_view(['GET'])
        @throttle_classes([OncePerDayUserThrottle])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = view(request)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
