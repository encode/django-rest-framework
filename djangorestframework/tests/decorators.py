from django.test import TestCase
from djangorestframework.response import Response
from djangorestframework.compat import RequestFactory
from djangorestframework.renderers import JSONRenderer
from djangorestframework.parsers import JSONParser
from djangorestframework.authentication import BasicAuthentication
from djangorestframework.throttling import SimpleRateThottle
from djangorestframework.permissions import IsAuthenticated
from djangorestframework.decorators import (
    api_view,
    renderer_classes,
    parser_classes,
    authentication_classes,
    throttle_classes,
    permission_classes,
    LazyViewCreator
)


class DecoratorTestCase(TestCase):

    def setUp(self):
        self.factory = RequestFactory()

    def test_wrap_view(self):

        @api_view(['GET'])
        def view(request):
            return Response({})

        self.assertTrue(isinstance(view, LazyViewCreator))

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

        @renderer_classes([JSONRenderer])
        @api_view(['GET'])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.renderer_classes, [JSONRenderer])

    def test_parser_classes(self):

        @parser_classes([JSONParser])
        @api_view(['GET'])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.request.parser_classes, [JSONParser])

    def test_authentication_classes(self):

        @authentication_classes([BasicAuthentication])
        @api_view(['GET'])
        def view(request):
            return Response({})

        request = self.factory.get('/')
        response = view(request)
        self.assertEqual(response.request.authentication_classes, [BasicAuthentication])

# Doesn't look like these bits are working quite yet

#    def test_throttle_classes(self):
#
#        @throttle_classes([SimpleRateThottle])
#        @api_view(['GET'])
#        def view(request):
#            return Response({})
#
#        request = self.factory.get('/')
#        response = view(request)
#        self.assertEqual(response.request.throttle, [SimpleRateThottle])

#    def test_permission_classes(self):

#        @permission_classes([IsAuthenticated])
#        @api_view(['GET'])
#        def view(request):
#            return Response({})

#        request = self.factory.get('/')
#        response = view(request)
#        self.assertEqual(response.request.permission_classes, [IsAuthenticated])
