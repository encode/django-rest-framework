from django.conf.urls import url
from rest_framework import versioning
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase


class RequestVersionView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'version': request.version})

class ReverseView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'url': reverse('another', request=request)})


factory = APIRequestFactory()

mock_view = lambda request: None

urlpatterns = [
    url(r'^another/$', mock_view, name='another')
]


class TestRequestVersion:
    def test_unversioned(self):
        view = RequestVersionView.as_view()

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'version': None}

    def test_query_param_versioning(self):
        scheme = versioning.QueryParameterVersioning
        view = RequestVersionView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/?version=1.2.3')
        response = view(request)
        assert response.data == {'version': '1.2.3'}

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'version': None}

    def test_host_name_versioning(self):
        scheme = versioning.HostNameVersioning
        view = RequestVersionView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_HOST='v1.example.org')
        response = view(request)
        assert response.data == {'version': 'v1'}

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'version': None}

    def test_accept_header_versioning(self):
        scheme = versioning.AcceptHeaderVersioning
        view = RequestVersionView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_ACCEPT='application/json; version=1.2.3')
        response = view(request)
        assert response.data == {'version': '1.2.3'}

        request = factory.get('/endpoint/', HTTP_ACCEPT='application/json')
        response = view(request)
        assert response.data == {'version': None}

    def test_url_path_versioning(self):
        scheme = versioning.URLPathVersioning
        view = RequestVersionView.as_view(versioning_class=scheme)

        request = factory.get('/1.2.3/endpoint/')
        response = view(request, version='1.2.3')
        assert response.data == {'version': '1.2.3'}

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'version': None}


class TestURLReversing(APITestCase):
    urls = 'tests.test_versioning'

    def test_reverse_unversioned(self):
        view = ReverseView.as_view()

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'url': 'http://testserver/another/'}

    def test_reverse_host_name_versioning(self):
        scheme = versioning.HostNameVersioning
        view = ReverseView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_HOST='v1.example.org')
        response = view(request)
        assert response.data == {'url': 'http://v1.example.org/another/'}

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'url': 'http://testserver/another/'}
