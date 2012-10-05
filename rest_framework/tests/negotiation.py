from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.negotiation import DefaultContentNegotiation
from rest_framework.response import Response

factory = RequestFactory()


class MockJSONRenderer(object):
    media_type = 'application/json'

    def __init__(self, view):
        pass


class MockHTMLRenderer(object):
    media_type = 'text/html'

    def __init__(self, view):
        pass


@api_view(('GET',))
@renderer_classes((MockJSONRenderer, MockHTMLRenderer))
def example(request):
    return Response()


class TestAcceptedMediaType(TestCase):
    def setUp(self):
        self.renderers = [MockJSONRenderer(None), MockHTMLRenderer(None)]
        self.negotiator = DefaultContentNegotiation()

    def negotiate(self, request):
        return self.negotiator.negotiate(request, self.renderers)

    def test_client_without_accept_use_renderer(self):
        request = factory.get('/')
        accepted_renderer, accepted_media_type = self.negotiate(request)
        self.assertEquals(accepted_media_type, 'application/json')

    def test_client_underspecifies_accept_use_renderer(self):
        request = factory.get('/', HTTP_ACCEPT='*/*')
        accepted_renderer, accepted_media_type = self.negotiate(request)
        self.assertEquals(accepted_media_type, 'application/json')

    def test_client_overspecifies_accept_use_client(self):
        request = factory.get('/', HTTP_ACCEPT='application/json; indent=8')
        accepted_renderer, accepted_media_type = self.negotiate(request)
        self.assertEquals(accepted_media_type, 'application/json; indent=8')


class IntegrationTests(TestCase):
    def test_accepted_negotiation_set_on_request(self):
        request = factory.get('/', HTTP_ACCEPT='*/*')
        response = example(request)
        self.assertEquals(response.accepted_media_type, 'application/json')
