from __future__ import unicode_literals

from collections import namedtuple

from django.conf.urls import include, url
from django.test import TestCase

from rest_framework.compat import RegexURLResolver, Resolver404
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
    def _resolve_urlpatterns(self, urlpatterns, test_paths):
        factory = APIRequestFactory()
        try:
            urlpatterns = format_suffix_patterns(urlpatterns)
        except Exception:
            self.fail("Failed to apply `format_suffix_patterns` on  the supplied urlpatterns")
        resolver = RegexURLResolver(r'^/', urlpatterns)
        for test_path in test_paths:
            request = factory.get(test_path.path)
            try:
                callback, callback_args, callback_kwargs = resolver.resolve(request.path_info)
            except Exception:
                self.fail("Failed to resolve URL: %s" % request.path_info)
            assert callback_args == test_path.args
            assert callback_kwargs == test_path.kwargs

    def test_trailing_slash(self):
        factory = APIRequestFactory()
        urlpatterns = format_suffix_patterns([
            url(r'^test/$', dummy_view),
        ])
        resolver = RegexURLResolver(r'^/', urlpatterns)

        test_paths = [
            (URLTestPath('/test.api', (), {'format': 'api'}), True),
            (URLTestPath('/test/.api', (), {'format': 'api'}), False),
            (URLTestPath('/test.api/', (), {'format': 'api'}), True),
        ]

        for test_path, expected_resolved in test_paths:
            request = factory.get(test_path.path)
            try:
                callback, callback_args, callback_kwargs = resolver.resolve(request.path_info)
            except Resolver404:
                callback, callback_args, callback_kwargs = (None, None, None)
            if not expected_resolved:
                assert callback is None
                continue

            assert callback_args == test_path.args
            assert callback_kwargs == test_path.kwargs

    def test_format_suffix(self):
        urlpatterns = [
            url(r'^test$', dummy_view),
        ]
        test_paths = [
            URLTestPath('/test', (), {}),
            URLTestPath('/test.api', (), {'format': 'api'}),
            URLTestPath('/test.asdf', (), {'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def test_default_args(self):
        urlpatterns = [
            url(r'^test$', dummy_view, {'foo': 'bar'}),
        ]
        test_paths = [
            URLTestPath('/test', (), {'foo': 'bar', }),
            URLTestPath('/test.api', (), {'foo': 'bar', 'format': 'api'}),
            URLTestPath('/test.asdf', (), {'foo': 'bar', 'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def test_included_urls(self):
        nested_patterns = [
            url(r'^path$', dummy_view)
        ]
        urlpatterns = [
            url(r'^test/', include(nested_patterns), {'foo': 'bar'}),
        ]
        test_paths = [
            URLTestPath('/test/path', (), {'foo': 'bar', }),
            URLTestPath('/test/path.api', (), {'foo': 'bar', 'format': 'api'}),
            URLTestPath('/test/path.asdf', (), {'foo': 'bar', 'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)
