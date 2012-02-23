from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from django.utils import simplejson as json

from djangorestframework.renderers import JSONRenderer
from djangorestframework.reverse import reverse, reverse_lazy
from djangorestframework.views import View


class ReverseView(View):
    """
    Mock resource which simply returns a URL, so that we can ensure
    that reversed URLs are fully qualified.
    """
    renderers = (JSONRenderer, )

    def get(self, request):
        return reverse('reverse', request=request)


class LazyView(View):
    """
    Mock resource which simply returns a URL, so that we can ensure
    that reversed URLs are fully qualified.
    """
    renderers = (JSONRenderer, )

    def get(self, request):
        return reverse_lazy('lazy', request=request)


urlpatterns = patterns('',
    url(r'^reverse$', ReverseView.as_view(), name='reverse'),
    url(r'^lazy$', LazyView.as_view(), name='lazy'),
)


class ReverseTests(TestCase):
    """
    Tests for fully qualifed URLs when using `reverse`.
    """
    urls = 'djangorestframework.tests.reverse'

    def test_reversed_urls_are_fully_qualified(self):
        response = self.client.get('/reverse')
        self.assertEqual(json.loads(response.content),
                        'http://testserver/reverse')

    #def test_reversed_lazy_urls_are_fully_qualified(self):
    #    response = self.client.get('/lazy')
    #    self.assertEqual(json.loads(response.content),
    #                     'http://testserver/lazy')
