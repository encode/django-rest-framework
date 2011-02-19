from djangorestframework.compat import View  # Use Django 1.3's django.views.generic.View, or fall back to a clone of that if Django < 1.3 
from djangorestframework.emitters import EmitterMixin, DEFAULT_EMITTERS
from djangorestframework.response import Response

from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import reverse


class ExampleView(EmitterMixin, View):
    """An example view using Django 1.3's class based views.
    Uses djangorestframework's EmitterMixin to provide support for multiple output formats."""
    emitters = DEFAULT_EMITTERS

    def get(self, request):
        response = Response(200, {'description': 'Some example content',
                                  'url': reverse('mixin-view')})
        return self.emit(response)


urlpatterns = patterns('',
    url(r'^$', ExampleView.as_view(), name='mixin-view'),
)

