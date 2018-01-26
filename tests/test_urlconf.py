"""
Test rest framework assumptions about the configuration of the root urlconf.
"""
from django.conf.urls import include, url

from rest_framework import routers, viewsets
from rest_framework.reverse import NoReverseMatch, reverse
from rest_framework.test import APITestCase, URLPatternsTestCase


class MockViewSet(viewsets.ViewSet):
    def list(self, request, *args, **kwargs):
        pass


router = routers.DefaultRouter(trailing_slash=False)
router.register(r'example', MockViewSet, base_name='example')


class TestUrlsAppNameRequired(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        url(r'^api/', include(router.urls)),
    ]

    def test_reverse(self):
        """
        The 'rest_framework' namespace must be present.
        """
        with self.assertRaises(NoReverseMatch):
            reverse('example-list')


class TestUrlpatternsAppName(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        url(r'^api/', include(router.urlpatterns)),
    ]

    def test_reverse(self):
        self.assertEqual(reverse('example-list'), '/api/example')

    def test_app_name_reverse(self):
        self.assertEqual(reverse('rest_framework:example-list'), '/api/example')


class TestUrlpatternsNamespace(APITestCase, URLPatternsTestCase):
    urlpatterns = [
        url(r'^api/v1/', include(router.urlpatterns, namespace='v1')),
        url(r'^api/v2/', include(router.urlpatterns, namespace='v2')),
    ]

    def test_reverse(self):
        self.assertEqual(reverse('example-list'), '/api/v2/example')

    def test_app_name_reverse(self):
        self.assertEqual(reverse('rest_framework:example-list'), '/api/v2/example')

    def test_namespace_reverse(self):
        self.assertEqual(reverse('v1:example-list'), '/api/v1/example')
        self.assertEqual(reverse('v2:example-list'), '/api/v2/example')


class TestAppUrlpatternsAppName(APITestCase, URLPatternsTestCase):
    apppatterns = ([
        url(r'^api/', include(router.urlpatterns)),
    ], 'api')

    urlpatterns = [
        url(r'^', include(apppatterns)),
    ]

    def test_reverse(self):
        """
        Nesting the router.urlpatterns in an app with an app_name will
        break url resolution.
        """
        with self.assertRaises(NoReverseMatch):
            reverse('example-list')


class TestAppUrlpatterns(APITestCase, URLPatternsTestCase):
    apppatterns = ([
        url(r'^api/', include(router.urlpatterns)),
    ], None)

    urlpatterns = [
        url(r'^', include(apppatterns)),
    ]

    def test_reverse(self):
        self.assertEqual(reverse('example-list'), '/api/example')


class TestAppUrlsAppName(APITestCase, URLPatternsTestCase):
    apppatterns = ([
        url(r'^api/', include(router.urls)),
    ], 'rest_framework')

    urlpatterns = [
        url(r'^', include(apppatterns)),
    ]

    def test_reverse(self):
        self.assertEqual(reverse('example-list'), '/api/example')

    def test_app_name_reverse(self):
        self.assertEqual(reverse('rest_framework:example-list'), '/api/example')


class TestAppUrlsNamespace(APITestCase, URLPatternsTestCase):
    apppatterns = ([
        url(r'^', include(router.urls)),
    ], 'rest_framework')

    urlpatterns = [
        url(r'^api/v1/', include(apppatterns, namespace='v1')),
        url(r'^api/v2/', include(apppatterns, namespace='v2')),
    ]

    def test_reverse(self):
        self.assertEqual(reverse('example-list'), '/api/v2/example')

    def test_app_name_reverse(self):
        self.assertEqual(reverse('rest_framework:example-list'), '/api/v2/example')

    def test_namespace_reverse(self):
        self.assertEqual(reverse('v1:example-list'), '/api/v1/example')
        self.assertEqual(reverse('v2:example-list'), '/api/v2/example')
