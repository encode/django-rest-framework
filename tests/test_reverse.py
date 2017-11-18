from __future__ import unicode_literals

from django.conf.urls import include, url
from django.http import HttpResponse
from django.test import TestCase, override_settings
from django.urls import NoReverseMatch

from rest_framework.reverse import current_app, reverse
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


def mock_view(request):
    return HttpResponse('')


apppatterns = ([
    url(r'^home$', mock_view, name='home'),
], 'app')


urlpatterns = [
    url(r'^view$', mock_view, name='view'),
    url(r'^app2/', include(apppatterns, namespace='app2')),
    url(r'^app1/', include(apppatterns, namespace='app1')),
]


class MockVersioningScheme(object):

    def __init__(self, raise_error=False):
        self.raise_error = raise_error

    def reverse(self, *args, **kwargs):
        if self.raise_error:
            raise NoReverseMatch()

        return 'http://scheme-reversed/view'


@override_settings(ROOT_URLCONF='tests.test_reverse')
class ReverseTests(TestCase):
    """
    Tests for fully qualified URLs when using `reverse`.
    """
    def test_reversed_urls_are_fully_qualified(self):
        request = factory.get('/view')
        url = reverse('view', request=request)
        assert url == 'http://testserver/view'

    def test_reverse_with_versioning_scheme(self):
        request = factory.get('/view')
        request.versioning_scheme = MockVersioningScheme()

        url = reverse('view', request=request)
        assert url == 'http://scheme-reversed/view'

    def test_reverse_with_versioning_scheme_fallback_to_default_on_error(self):
        request = factory.get('/view')
        request.versioning_scheme = MockVersioningScheme(raise_error=True)

        url = reverse('view', request=request)
        assert url == 'http://testserver/view'


@override_settings(ROOT_URLCONF='tests.test_reverse')
class NamespaceTests(TestCase):
    """
    Ensure reverse can handle namespaces.

    Note: It's necessary to use self.client() here, as the
          RequestFactory does not setup the resolver_match.
    """

    def request(self, url):
        return self.client.get(url).wsgi_request

    def test_application_namespace(self):
        url = reverse('app:home')
        assert url == '/app1/home'

        # instance namespace provided by current_app
        url = reverse('app:home', current_app='app2')
        assert url == '/app2/home'

    def test_instance_namespace(self):
        url = reverse('app1:home')
        assert url == '/app1/home'

        url = reverse('app2:home')
        assert url == '/app2/home'

    def test_application_namespace_with_request(self):
        # request's current app affects result
        request1 = self.request('/app1/home')
        request2 = self.request('/app2/home')

        # sanity check
        assert current_app(request1) == 'app1'
        assert current_app(request2) == 'app2'

        assert reverse('app:home', request=request1) == 'http://testserver/app1/home'
        assert reverse('app:home', request=request2) == 'http://testserver/app2/home'

    def test_instance_namespace_with_request(self):
        # request's current app is not relevant
        request1 = self.request('/app1/home')
        request2 = self.request('/app2/home')

        # sanity check
        assert current_app(request1) == 'app1'
        assert current_app(request2) == 'app2'

        assert reverse('app1:home', request=request1) == 'http://testserver/app1/home'
        assert reverse('app2:home', request=request1) == 'http://testserver/app2/home'
        assert reverse('app1:home', request=request2) == 'http://testserver/app1/home'
        assert reverse('app2:home', request=request2) == 'http://testserver/app2/home'


@override_settings(ROOT_URLCONF='tests.test_reverse')
class CurrentAppTests(TestCase):
    """
    Test current_app() function.

    Note: It's necessary to use self.client() here, as the
          RequestFactory does not setup the resolver_match.
    """

    def request(self, url):
        return self.client.get(url).wsgi_request

    def test_no_namespace(self):
        request = self.request('/view')
        assert current_app(request) == ''

    def test_namespace(self):
        request = self.request('/app1/home')
        assert current_app(request) == 'app1'

        request = self.request('/app2/home')
        assert current_app(request) == 'app2'

    def test_factory_incompatibility(self):
        request = factory.get('/app1/home')
        assert current_app(request) is None
