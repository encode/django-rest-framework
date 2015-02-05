from .utils import MockObject, MockQueryset, UsingURLPatterns
from django.conf.urls import include, url
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework import status, versioning
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.versioning import NamespaceVersioning
import pytest


class RequestVersionView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'version': request.version})


class ReverseView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'url': reverse('another', request=request)})


class RequestInvalidVersionView(APIView):
    def determine_version(self, request, *args, **kwargs):
        scheme = self.versioning_class()
        scheme.allowed_versions = ('v1', 'v2')
        return (scheme.determine_version(request, *args, **kwargs), scheme)

    def get(self, request, *args, **kwargs):
        return Response({'version': request.version})


factory = APIRequestFactory()

mock_view = lambda request: None
dummy_view = lambda request, pk: None


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

    def test_namespace_versioning(self):
        class FakeResolverMatch:
            namespace = 'v1'

        scheme = versioning.NamespaceVersioning
        view = RequestVersionView.as_view(versioning_class=scheme)

        request = factory.get('/v1/endpoint/')
        request.resolver_match = FakeResolverMatch
        response = view(request, version='v1')
        assert response.data == {'version': 'v1'}

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'version': None}


class TestURLReversing(UsingURLPatterns, APITestCase):
    included = [
        url(r'^namespaced/$', mock_view, name='another'),
        url(r'^example/(?P<pk>\d+)/$', dummy_view, name='example-detail')
    ]

    urlpatterns = [
        url(r'^v1/', include(included, namespace='v1')),
        url(r'^another/$', mock_view, name='another'),
        url(r'^(?P<version>[^/]+)/another/$', mock_view, name='another'),
    ]

    def test_reverse_unversioned(self):
        view = ReverseView.as_view()

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'url': 'http://testserver/another/'}

    def test_reverse_query_param_versioning(self):
        scheme = versioning.QueryParameterVersioning
        view = ReverseView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/?version=v1')
        response = view(request)
        assert response.data == {'url': 'http://testserver/another/?version=v1'}

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

    def test_reverse_url_path_versioning(self):
        scheme = versioning.URLPathVersioning
        view = ReverseView.as_view(versioning_class=scheme)

        request = factory.get('/v1/endpoint/')
        response = view(request, version='v1')
        assert response.data == {'url': 'http://testserver/v1/another/'}

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'url': 'http://testserver/another/'}

    def test_reverse_namespace_versioning(self):
        class FakeResolverMatch:
            namespace = 'v1'

        scheme = versioning.NamespaceVersioning
        view = ReverseView.as_view(versioning_class=scheme)

        request = factory.get('/v1/endpoint/')
        request.resolver_match = FakeResolverMatch
        response = view(request, version='v1')
        assert response.data == {'url': 'http://testserver/v1/namespaced/'}

        request = factory.get('/endpoint/')
        response = view(request)
        assert response.data == {'url': 'http://testserver/another/'}


class TestInvalidVersion:
    def test_invalid_query_param_versioning(self):
        scheme = versioning.QueryParameterVersioning
        view = RequestInvalidVersionView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/?version=v3')
        response = view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_host_name_versioning(self):
        scheme = versioning.HostNameVersioning
        view = RequestInvalidVersionView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_HOST='v3.example.org')
        response = view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_accept_header_versioning(self):
        scheme = versioning.AcceptHeaderVersioning
        view = RequestInvalidVersionView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_ACCEPT='application/json; version=v3')
        response = view(request)
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE

    def test_invalid_url_path_versioning(self):
        scheme = versioning.URLPathVersioning
        view = RequestInvalidVersionView.as_view(versioning_class=scheme)

        request = factory.get('/v3/endpoint/')
        response = view(request, version='v3')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_namespace_versioning(self):
        class FakeResolverMatch:
            namespace = 'v3'

        scheme = versioning.NamespaceVersioning
        view = RequestInvalidVersionView.as_view(versioning_class=scheme)

        request = factory.get('/v3/endpoint/')
        request.resolver_match = FakeResolverMatch
        response = view(request, version='v3')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestHyperlinkedRelatedField(UsingURLPatterns, APITestCase):
    included = [
        url(r'^namespaced/(?P<pk>\d+)/$', mock_view, name='namespaced'),
    ]

    urlpatterns = [
        url(r'^v1/', include(included, namespace='v1')),
        url(r'^v2/', include(included, namespace='v2'))
    ]

    def setUp(self):
        super(TestHyperlinkedRelatedField, self).setUp()

        class HyperlinkedMockQueryset(MockQueryset):
            def get(self, **lookup):
                for item in self.items:
                    if item.pk == int(lookup.get('pk', -1)):
                        return item
                raise ObjectDoesNotExist()

        self.queryset = HyperlinkedMockQueryset([
            MockObject(pk=1, name='foo'),
            MockObject(pk=2, name='bar'),
            MockObject(pk=3, name='baz')
        ])
        self.field = serializers.HyperlinkedRelatedField(
            view_name='namespaced',
            queryset=self.queryset
        )
        request = factory.post('/', urlconf='tests.test_versioning')
        request.versioning_scheme = NamespaceVersioning()
        request.version = 'v1'
        self.field._context = {'request': request}

    def test_bug_2489(self):
        self.field.to_internal_value('/v1/namespaced/3/')
        with pytest.raises(serializers.ValidationError):
            self.field.to_internal_value('/v2/namespaced/3/')
