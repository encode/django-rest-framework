from __future__ import unicode_literals
from django.conf.urls import patterns, url
from django.test import TestCase
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


def null_view(request):
    pass

urlpatterns = patterns(
    '',
    url(r'^view$', null_view, name='view'),
)


class ReverseTests(TestCase):
    """
    Tests for fully qualified URLs when using `reverse`.
    """
    urls = 'tests.test_reverse'

    def test_reversed_urls_are_fully_qualified(self):
        request = factory.get('/view')
        url = reverse('view', request=request)
        self.assertEqual(url, 'http://testserver/view')
