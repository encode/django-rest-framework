from .utils import UsingURLPatterns
from django.conf.urls import include, url
from rest_framework import serializers
from rest_framework import status, versioning
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase
from rest_framework.versioning import NamespaceVersioning
from rest_framework.relations import PKOnlyObject
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


def dummy_view(request):
    pass


def dummy_pk_view(request, pk):
    pass


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
        url(r'^namespaced/$', dummy_view, name='another'),
        url(r'^example/(?P<pk>\d+)/$', dummy_pk_view, name='example-detail')
    ]

    urlpatterns = [
        url(r'^v1/', include(included, namespace='v1')),
        url(r'^another/$', dummy_view, name='another'),
        url(r'^(?P<version>[^/]+)/another/$', dummy_view, name='another'),
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
        url(r'^namespaced/(?P<pk>\d+)/$', dummy_pk_view, name='namespaced'),
    ]

    urlpatterns = [
        url(r'^v1/', include(included, namespace='v1')),
        url(r'^v2/', include(included, namespace='v2'))
    ]

    def setUp(self):
        super(TestHyperlinkedRelatedField, self).setUp()

        class MockQueryset(object):
            def get(self, pk):
                return 'object %s' % pk

        self.field = serializers.HyperlinkedRelatedField(
            view_name='namespaced',
            queryset=MockQueryset()
        )
        request = factory.get('/')
        request.versioning_scheme = NamespaceVersioning()
        request.version = 'v1'
        self.field._context = {'request': request}

    def test_bug_2489(self):
        assert self.field.to_internal_value('/v1/namespaced/3/') == 'object 3'
        with pytest.raises(serializers.ValidationError):
            self.field.to_internal_value('/v2/namespaced/3/')


class TestNamespaceVersioningHyperlinkedRelatedFieldScheme(UsingURLPatterns, APITestCase):
    included = [
        url(r'^namespaced/(?P<pk>\d+)/$', dummy_pk_view, name='namespaced'),
    ]

    urlpatterns = [
        url(r'^v1/', include(included, namespace='v1')),
        url(r'^v2/', include(included, namespace='v2')),
        url(r'^non-api/(?P<pk>\d+)/$', dummy_pk_view, name='non-api-view')
    ]

    def _create_field(self, view_name, version):
        request = factory.get("/")
        request.versioning_scheme = NamespaceVersioning()
        request.version = version

        field = serializers.HyperlinkedRelatedField(
            view_name=view_name,
            read_only=True)
        field._context = {'request': request}
        return field

    def test_api_url_is_properly_reversed_with_v1(self):
        field = self._create_field('namespaced', 'v1')
        assert field.to_representation(PKOnlyObject(3)) == 'http://testserver/v1/namespaced/3/'

    def test_api_url_is_properly_reversed_with_v2(self):
        field = self._create_field('namespaced', 'v2')
        assert field.to_representation(PKOnlyObject(5)) == 'http://testserver/v2/namespaced/5/'

    def test_non_api_url_is_properly_reversed_regardless_of_the_version(self):
        """
        Regression test for #2711
        """
        field = self._create_field('non-api-view', 'v1')
        assert field.to_representation(PKOnlyObject(10)) == 'http://testserver/non-api/10/'

        field = self._create_field('non-api-view', 'v2')
        assert field.to_representation(PKOnlyObject(10)) == 'http://testserver/non-api/10/'
