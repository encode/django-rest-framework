from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from django.utils import simplejson as json

from djangorestframework.renderers import JSONRenderer
from djangorestframework.reverse import reverse
from djangorestframework.views import View


class MyView(View):
    """
    Mock resource which simply returns a URL, so that we can ensure
    that reversed URLs are fully qualified.
    """
    renderers = (JSONRenderer, )

    def get(self, request):
        return reverse('myview', request=request)

urlpatterns = patterns('',
    url(r'^myview$', MyView.as_view(), name='myview'),
)


class ReverseTests(TestCase):
    """
    Tests for fully qualifed URLs when using `reverse`.
    """
    urls = 'djangorestframework.tests.reverse'

    def test_reversed_urls_are_fully_qualified(self):
        response = self.client.get('/myview')
        self.assertEqual(json.loads(response.content), 'http://testserver/myview')
