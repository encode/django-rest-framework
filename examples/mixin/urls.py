from djangorestframework.compat import View  # Use Django 1.3's django.views.generic.View, or fall back to a clone of that if Django < 1.3
from djangorestframework.mixins import ResponseMixin
from djangorestframework.renderers import DEFAULT_RENDERERS
from djangorestframework.response import Response

from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse


class ExampleView(ResponseMixin, View):
    """An example view using Django 1.3's class based views.
    Uses djangorestframework's RendererMixin to provide support for multiple output formats."""
    renderers = DEFAULT_RENDERERS

    def get(self, request):
        response = Response(200, {'description': 'Some example content',
                                  'url': reverse('mixin-view')})
        return self.render(response)


urlpatterns = patterns('',
    url(r'^$', ExampleView.as_view(), name='mixin-view'),
)

