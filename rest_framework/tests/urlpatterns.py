from __future__ import unicode_literals
from collections import namedtuple
from django.core import urlresolvers
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework.compat import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns


# A container class for test paths for the test case
URLTestPath = namedtuple('URLTestPath', ['path', 'args', 'kwargs'])


def dummy_view(request, *args, **kwargs):
    pass


class FormatSuffixTests(TestCase):
    """
    Tests `format_suffix_patterns` against different URLPatterns to ensure the URLs still resolve properly, including any captured parameters.
    """
    def _resolve_urlpatterns(self, urlpatterns, test_paths):
        factory = RequestFactory()
        try:
            urlpatterns = format_suffix_patterns(urlpatterns)
        except Exception:
            self.fail("Failed to apply `format_suffix_patterns` on  the supplied urlpatterns")
        resolver = urlresolvers.RegexURLResolver(r'^/', urlpatterns)
        for test_path in test_paths:
            request = factory.get(test_path.path)
            try:
                callback, callback_args, callback_kwargs = resolver.resolve(request.path_info)
            except Exception:
                self.fail("Failed to resolve URL: %s" % request.path_info)
            self.assertEqual(callback_args, test_path.args)
            self.assertEqual(callback_kwargs, test_path.kwargs)

    def test_format_suffix(self):
        urlpatterns = patterns(
            '',
            url(r'^test$', dummy_view),
        )
        test_paths = [
            URLTestPath('/test', (), {}),
            URLTestPath('/test.api', (), {'format': 'api'}),
            URLTestPath('/test.asdf', (), {'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def test_default_args(self):
        urlpatterns = patterns(
            '',
            url(r'^test$', dummy_view, {'foo': 'bar'}),
        )
        test_paths = [
            URLTestPath('/test', (), {'foo': 'bar', }),
            URLTestPath('/test.api', (), {'foo': 'bar', 'format': 'api'}),
            URLTestPath('/test.asdf', (), {'foo': 'bar', 'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)

    def test_included_urls(self):
        nested_patterns = patterns(
            '',
            url(r'^path$', dummy_view)
        )
        urlpatterns = patterns(
            '',
            url(r'^test/', include(nested_patterns), {'foo': 'bar'}),
        )
        test_paths = [
            URLTestPath('/test/path', (), {'foo': 'bar', }),
            URLTestPath('/test/path.api', (), {'foo': 'bar', 'format': 'api'}),
            URLTestPath('/test/path.asdf', (), {'foo': 'bar', 'format': 'asdf'}),
        ]
        self._resolve_urlpatterns(urlpatterns, test_paths)
