from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework.compat import patterns, url
from rest_framework.reverse import reverse

factory = RequestFactory()


def null_view(request):
    pass

urlpatterns = patterns('',
    url(r'^view$', null_view, name='view'),
)


class ReverseTests(TestCase):
    """
    Tests for fully qualifed URLs when using `reverse`.
    """
    urls = 'rest_framework.tests.reverse'

    def test_reversed_urls_are_fully_qualified(self):
        request = factory.get('/view')
        url = reverse('view', request=request)
        self.assertEqual(url, 'http://testserver/view')
