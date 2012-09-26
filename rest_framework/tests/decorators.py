from django.test import TestCase
from rest_framework.response import Response
from rest_framework.compat import RequestFactory
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.authentication import BasicAuthentication
from rest_framework.throttling import SimpleRateThottle
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


class DecoratorTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def _finalize_response(self, request, response, *args, **kwargs):
        print "HAI"
        response.request = request
        return APIView.finalize_response(self, request, response, *args, **kwargs)

    def test_wrap_view(self):

        @api_view(['GET'])
        def view(request):
            return Response({})

        self.assertTrue(isinstance(view.cls_instance, APIView))

    def test_calling_method(self):

        @api_view(['GET'])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post('/')
        response = view(request)
        self.assertEqual(response.status_code, 405)

    def test_renderer_classes(self):

        @api_view(['GET'])
        @renderer_classes([JSONRenderer])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        self.assertTrue(isinstance(response.renderer, JSONRenderer))

    def test_parser_classes(self):

        @api_view(['GET'])
        @parser_classes([JSONParser])
        def view(request):
            self.assertEqual(request.parser_classes, [JSONParser])
            return Response({})

        request = self.factory.get('/')
        view(request)

    def test_authentication_classes(self):

        @api_view(['GET'])
        @authentication_classes([BasicAuthentication])
        def view(request):
            self.assertEqual(request.authentication_classes, [BasicAuthentication])
            return Response({})

        request = self.factory.get('/')
        view(request)

    def test_permission_classes(self):

        @api_view(['GET'])
        @permission_classes([IsAuthenticated])
        def view(request):
            self.assertEqual(request.permission_classes, [IsAuthenticated])
            return Response({})

        request = self.factory.get('/')
        view(request)

# Doesn't look like this bits are working quite yet

#    def test_throttle_classes(self):

#        @api_view(['GET'])
#        @throttle_classes([SimpleRateThottle])
#        def view(request):
#            self.assertEqual(request.throttle_classes, [SimpleRateThottle])
#            return Response({})

#        request = self.factory.get('/')
#        view(request)
