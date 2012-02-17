from django.conf.urls.defaults import patterns, url
from requestexample.views import RequestExampleView, EchoRequestContentView
from examples.views import ProxyView


urlpatterns = patterns('',
    url(r'^$', RequestExampleView.as_view(), name='request-example'),
    url(r'^content$', ProxyView.as_view(view_class=EchoRequestContentView), name='request-content'),
)
