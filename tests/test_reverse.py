from django.test import TestCase, override_settings
from django.urls import NoReverseMatch, path

from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


def null_view(request):
    pass


urlpatterns = [
    path('view', null_view, name='view'),
]


class MockVersioningScheme:

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
