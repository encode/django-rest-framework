from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.compat import patterns, url, include
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


def null_view(request):
    pass


v0_urlpatterns = patterns('',
    url(r'^view$', null_view, name='view'),
    url(r'^other-view', null_view, name="other-view"),
)

v1_urlpatterns = patterns('',
    url(r'^view$', null_view, name='view'),
)

v2_urlpatterns = patterns('',
    url(r'^view$', null_view, name='view'),
)

urlpatterns = patterns('',
    url(r'', include(v0_urlpatterns)),  # Un-versioned.
    url(r'v1/', include(v1_urlpatterns, namespace='v1')),
    url(r'v2/', include(v2_urlpatterns, namespace='v2')),
)


class ReverseTests(TestCase):
    """
    Tests for fully qualified URLs when using `reverse`.
    """
    urls = 'rest_framework.tests.test_reverse'

    def test_reversed_urls_are_fully_qualified(self):
        request = factory.get('/view')
        url = reverse('view', request=request)
        self.assertEqual(url, 'http://testserver/view')


    def test_namespaced_request_to_non_namespaced_view(self):
        """
        Main test for #1143.

        (Code moved unchanged to v2 will reverse to v2.)
        """
        request = factory.get('/v2/view')
        url = reverse('view', request=request)
        self.assertEqual(url, 'http://testserver/v2/view')

    def test_namespaced_request_to_non_namespaced_view_not_in_namespace(self):
        request = factory.get('/v2/view')
        url = reverse('other-view', request=request)
        self.assertEqual(url, 'http://testserver/other-view')


    # Additional tests for #1143
    # Covering cases mentioned
    # https://github.com/tomchristie/django-rest-framework/pull/1143#issuecomment-30031591
    def test_non_namespaced_request_to_namespaced_view(self):
        request = factory.get('/view')
        url = reverse('v2:view', request=request)
        self.assertEqual(url, 'http://testserver/v2/view')

    def test_namespaced_request_to_same_namespaced_view(self):
        request = factory.get('/v2/view')
        url = reverse('v2:view', request=request)
        self.assertEqual(url, 'http://testserver/v2/view')

    def test_namespaced_request_to_different_namespaced_view(self):
        request = factory.get('/v2/view')
        url = reverse('v1:view', request=request)
        self.assertEqual(url, 'http://testserver/v1/view')