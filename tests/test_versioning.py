import pytest
from django.test import override_settings
from django.urls import include, path, re_path

from rest_framework import serializers, status, versioning
from rest_framework.decorators import APIView
from rest_framework.relations import PKOnlyObject
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.test import (
    APIRequestFactory, APITestCase, URLPatternsTestCase
)
from rest_framework.versioning import NamespaceVersioning


class RequestVersionView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'version': request.version})


class ReverseView(APIView):
    def get(self, request, *args, **kwargs):
        return Response({'url': reverse('another', request=request)})


class AllowedVersionsView(RequestVersionView):
    def determine_version(self, request, *args, **kwargs):
        scheme = self.versioning_class()
        scheme.allowed_versions = ('v1', 'v2')
        return (scheme.determine_version(request, *args, **kwargs), scheme)


class AllowedAndDefaultVersionsView(RequestVersionView):
    def determine_version(self, request, *args, **kwargs):
        scheme = self.versioning_class()
        scheme.allowed_versions = ('v1', 'v2')
        scheme.default_version = 'v2'
        return (scheme.determine_version(request, *args, **kwargs), scheme)


class AllowedWithNoneVersionsView(RequestVersionView):
    def determine_version(self, request, *args, **kwargs):
        scheme = self.versioning_class()
        scheme.allowed_versions = ('v1', 'v2', None)
        return (scheme.determine_version(request, *args, **kwargs), scheme)


class AllowedWithNoneAndDefaultVersionsView(RequestVersionView):
    def determine_version(self, request, *args, **kwargs):
        scheme = self.versioning_class()
        scheme.allowed_versions = ('v1', 'v2', None)
        scheme.default_version = 'v2'
        return (scheme.determine_version(request, *args, **kwargs), scheme)


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

    @override_settings(ALLOWED_HOSTS=['*'])
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

        request = factory.get('/endpoint/', HTTP_ACCEPT='*/*; version=1.2.3')
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


class TestURLReversing(URLPatternsTestCase, APITestCase):
    included = [
        path('namespaced/', dummy_view, name='another'),
        path('example/<int:pk>/', dummy_pk_view, name='example-detail')
    ]

    urlpatterns = [
        path('v1/', include((included, 'v1'), namespace='v1')),
        path('another/', dummy_view, name='another'),
        re_path(r'^(?P<version>[v1|v2]+)/another/$', dummy_view, name='another'),
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

    @override_settings(ALLOWED_HOSTS=['*'])
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
        view = AllowedVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/?version=v3')
        response = view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @override_settings(ALLOWED_HOSTS=['*'])
    def test_invalid_host_name_versioning(self):
        scheme = versioning.HostNameVersioning
        view = AllowedVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_HOST='v3.example.org')
        response = view(request)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_accept_header_versioning(self):
        scheme = versioning.AcceptHeaderVersioning
        view = AllowedVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_ACCEPT='application/json; version=v3')
        response = view(request)
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE

    def test_invalid_url_path_versioning(self):
        scheme = versioning.URLPathVersioning
        view = AllowedVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/v3/endpoint/')
        response = view(request, version='v3')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_namespace_versioning(self):
        class FakeResolverMatch:
            namespace = 'v3'

        scheme = versioning.NamespaceVersioning
        view = AllowedVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/v3/endpoint/')
        request.resolver_match = FakeResolverMatch
        response = view(request, version='v3')
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAllowedAndDefaultVersion:
    def test_missing_without_default(self):
        scheme = versioning.AcceptHeaderVersioning
        view = AllowedVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_ACCEPT='application/json')
        response = view(request)
        assert response.status_code == status.HTTP_406_NOT_ACCEPTABLE

    def test_missing_with_default(self):
        scheme = versioning.AcceptHeaderVersioning
        view = AllowedAndDefaultVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_ACCEPT='application/json')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'version': 'v2'}

    def test_with_default(self):
        scheme = versioning.AcceptHeaderVersioning
        view = AllowedAndDefaultVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/',
                              HTTP_ACCEPT='application/json; version=v2')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK

    def test_missing_without_default_but_none_allowed(self):
        scheme = versioning.AcceptHeaderVersioning
        view = AllowedWithNoneVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_ACCEPT='application/json')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'version': None}

    def test_missing_with_default_and_none_allowed(self):
        scheme = versioning.AcceptHeaderVersioning
        view = AllowedWithNoneAndDefaultVersionsView.as_view(versioning_class=scheme)

        request = factory.get('/endpoint/', HTTP_ACCEPT='application/json')
        response = view(request)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'version': 'v2'}


class TestHyperlinkedRelatedField(URLPatternsTestCase, APITestCase):
    included = [
        path('namespaced/<int:pk>/', dummy_pk_view, name='namespaced'),
    ]

    urlpatterns = [
        path('v1/', include((included, 'v1'), namespace='v1')),
        path('v2/', include((included, 'v2'), namespace='v2'))
    ]

    def setUp(self):
        super().setUp()

        class MockQueryset:
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


class TestNamespaceVersioningHyperlinkedRelatedFieldScheme(URLPatternsTestCase, APITestCase):
    nested = [
        path('namespaced/<int:pk>/', dummy_pk_view, name='nested'),
    ]
    included = [
        path('namespaced/<int:pk>/', dummy_pk_view, name='namespaced'),
        path('nested/', include((nested, 'nested-namespace'), namespace='nested-namespace'))
    ]

    urlpatterns = [
        path('v1/', include((included, 'restframeworkv1'), namespace='v1')),
        path('v2/', include((included, 'restframeworkv2'), namespace='v2')),
        path('non-api/<int:pk>/', dummy_pk_view, name='non-api-view')
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

    def test_api_url_is_properly_reversed_with_nested(self):
        field = self._create_field('nested', 'v1:nested-namespace')
        assert field.to_representation(PKOnlyObject(3)) == 'http://testserver/v1/nested/namespaced/3/'

    def test_non_api_url_is_properly_reversed_regardless_of_the_version(self):
        """
        Regression test for #2711
        """
        field = self._create_field('non-api-view', 'v1')
        assert field.to_representation(PKOnlyObject(10)) == 'http://testserver/non-api/10/'

        field = self._create_field('non-api-view', 'v2')
        assert field.to_representation(PKOnlyObject(10)) == 'http://testserver/non-api/10/'
