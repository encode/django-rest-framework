import unittest
from collections import namedtuple

from django.conf.urls import include, url
from django.test import TestCase
from django.urls import Resolver404, path, re_path

from rest_framework.compat import make_url_resolver
from rest_framework.test import APIRequestFactory
from rest_framework.urlpatterns import format_suffix_patterns

# A container class for test paths for the test case
URLTestPath = namedtuple('URLTestPath', ['path', 'args', 'kwargs'])


def dummy_view(request, *args, **kwargs):
    pass


class FormatSuffixTests(TestCase):
    """
    Tests `format_suffix_patterns` against different URLPatterns to ensure the
    URLs still resolve properly, including any captured parameters.
    """
    def _resolve_urlpatterns(self, urlpatterns, test_paths, allowed=None):
        factory = APIRequestFactory()
        try:
            urlpatterns = format_suffix_patterns(urlpatterns, allowed=allowed)
        except Exception:
            self.fail("Failed to apply `format_suffix_patterns` on  the supplied urlpatterns")
        resolver = make_url_resolver(r'^/', urlpatterns)
        for test_path in test_paths:
            try:
                test_path, expected_resolved = test_path
            except (TypeError, ValueError):
                expected_resolved = True

            request = factory.get(test_path.path)
            try:
                callback, callback_args, callback_kwargs = resolver.resolve(request.path_info)
            except Resolver404:
                callback, callback_args, callback_kwargs = (None, None, None)
                if expected_resolved:
                    raise
            except Exception:
                self.fail("Failed to resolve URL: %s" % request.path_info)

            if not expected_resolved:
                assert callback is None
                continue

            assert callback_args == test_path.args
            assert callback_kwargs == test_path.kwargs

    def _test_trailing_slash(self, urlpatterns):
        test_paths = [
            (URLTestPath('/test.api', (), {'format': 'api'}), True),
            (URLTestPath('/test/.api', (), {'format': 'api'}), False),
            (URLTestPath('/test.api/', (), {'format': 'api'}), True),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def test_trailing_slash(self):
        urlpatterns = [
            url(r'^test/$', dummy_view),
        ]
        self._test_trailing_slash(urlpatterns)

    @unittest.skipUnless(path, 'needs Django 2')
    def test_trailing_slash_django2(self):
        urlpatterns = [
            path('test/', dummy_view),
        ]
        self._test_trailing_slash(urlpatterns)

    def _test_format_suffix(self, urlpatterns):
        test_paths = [
            URLTestPath('/test', (), {}),
            URLTestPath('/test.api', (), {'format': 'api'}),
            URLTestPath('/test.asdf', (), {'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def test_format_suffix(self):
        urlpatterns = [
            url(r'^test$', dummy_view),
        ]
        self._test_format_suffix(urlpatterns)

    @unittest.skipUnless(path, 'needs Django 2')
    def test_format_suffix_django2(self):
        urlpatterns = [
            path('test', dummy_view),
        ]
        self._test_format_suffix(urlpatterns)

    @unittest.skipUnless(path, 'needs Django 2')
    def test_format_suffix_django2_args(self):
        urlpatterns = [
            path('convtest/<int:pk>', dummy_view),
            re_path(r'^retest/(?P<pk>[0-9]+)$', dummy_view),
        ]
        test_paths = [
            URLTestPath('/convtest/42', (), {'pk': 42}),
            URLTestPath('/convtest/42.api', (), {'pk': 42, 'format': 'api'}),
            URLTestPath('/convtest/42.asdf', (), {'pk': 42, 'format': 'asdf'}),
            URLTestPath('/retest/42', (), {'pk': '42'}),
            URLTestPath('/retest/42.api', (), {'pk': '42', 'format': 'api'}),
            URLTestPath('/retest/42.asdf', (), {'pk': '42', 'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def _test_default_args(self, urlpatterns):
        test_paths = [
            URLTestPath('/test', (), {'foo': 'bar', }),
            URLTestPath('/test.api', (), {'foo': 'bar', 'format': 'api'}),
            URLTestPath('/test.asdf', (), {'foo': 'bar', 'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def test_default_args(self):
        urlpatterns = [
            url(r'^test$', dummy_view, {'foo': 'bar'}),
        ]
        self._test_default_args(urlpatterns)

    @unittest.skipUnless(path, 'needs Django 2')
    def test_default_args_django2(self):
        urlpatterns = [
            path('test', dummy_view, {'foo': 'bar'}),
        ]
        self._test_default_args(urlpatterns)

    def _test_included_urls(self, urlpatterns):
        test_paths = [
            URLTestPath('/test/path', (), {'foo': 'bar', }),
            URLTestPath('/test/path.api', (), {'foo': 'bar', 'format': 'api'}),
            URLTestPath('/test/path.asdf', (), {'foo': 'bar', 'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def test_included_urls(self):
        nested_patterns = [
            url(r'^path$', dummy_view)
        ]
        urlpatterns = [
            url(r'^test/', include(nested_patterns), {'foo': 'bar'}),
        ]
        self._test_included_urls(urlpatterns)

    @unittest.skipUnless(path, 'needs Django 2')
    def test_included_urls_django2(self):
        nested_patterns = [
            path('path', dummy_view)
        ]
        urlpatterns = [
            path('test/', include(nested_patterns), {'foo': 'bar'}),
        ]
        self._test_included_urls(urlpatterns)

    @unittest.skipUnless(path, 'needs Django 2')
    def test_included_urls_django2_mixed(self):
        nested_patterns = [
            path('path', dummy_view)
        ]
        urlpatterns = [
            url('^test/', include(nested_patterns), {'foo': 'bar'}),
        ]
        self._test_included_urls(urlpatterns)

    @unittest.skipUnless(path, 'needs Django 2')
    def test_included_urls_django2_mixed_args(self):
        nested_patterns = [
            path('path/<int:child>', dummy_view),
            url('^url/(?P<child>[0-9]+)$', dummy_view)
        ]
        urlpatterns = [
            url('^purl/(?P<parent>[0-9]+)/', include(nested_patterns), {'foo': 'bar'}),
            path('ppath/<int:parent>/', include(nested_patterns), {'foo': 'bar'}),
        ]
        test_paths = [
            # parent url() nesting child path()
            URLTestPath('/purl/87/path/42', (), {'parent': '87', 'child': 42, 'foo': 'bar', }),
            URLTestPath('/purl/87/path/42.api', (), {'parent': '87', 'child': 42, 'foo': 'bar', 'format': 'api'}),
            URLTestPath('/purl/87/path/42.asdf', (), {'parent': '87', 'child': 42, 'foo': 'bar', 'format': 'asdf'}),

            # parent path() nesting child url()
            URLTestPath('/ppath/87/url/42', (), {'parent': 87, 'child': '42', 'foo': 'bar', }),
            URLTestPath('/ppath/87/url/42.api', (), {'parent': 87, 'child': '42', 'foo': 'bar', 'format': 'api'}),
            URLTestPath('/ppath/87/url/42.asdf', (), {'parent': 87, 'child': '42', 'foo': 'bar', 'format': 'asdf'}),

            # parent path() nesting child path()
            URLTestPath('/ppath/87/path/42', (), {'parent': 87, 'child': 42, 'foo': 'bar', }),
            URLTestPath('/ppath/87/path/42.api', (), {'parent': 87, 'child': 42, 'foo': 'bar', 'format': 'api'}),
            URLTestPath('/ppath/87/path/42.asdf', (), {'parent': 87, 'child': 42, 'foo': 'bar', 'format': 'asdf'}),

            # parent url() nesting child url()
            URLTestPath('/purl/87/url/42', (), {'parent': '87', 'child': '42', 'foo': 'bar', }),
            URLTestPath('/purl/87/url/42.api', (), {'parent': '87', 'child': '42', 'foo': 'bar', 'format': 'api'}),
            URLTestPath('/purl/87/url/42.asdf', (), {'parent': '87', 'child': '42', 'foo': 'bar', 'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def _test_allowed_formats(self, urlpatterns):
        allowed_formats = ['good', 'ugly']
        test_paths = [
            (URLTestPath('/test.good/', (), {'format': 'good'}), True),
            (URLTestPath('/test.bad', (), {}), False),
            (URLTestPath('/test.ugly', (), {'format': 'ugly'}), True),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths, allowed=allowed_formats)

    def test_allowed_formats(self):
        urlpatterns = [
            url('^test$', dummy_view),
        ]
        self._test_allowed_formats(urlpatterns)

    @unittest.skipUnless(path, 'needs Django 2')
    def test_allowed_formats_django2(self):
        urlpatterns = [
            path('test', dummy_view),
        ]
        self._test_allowed_formats(urlpatterns)
