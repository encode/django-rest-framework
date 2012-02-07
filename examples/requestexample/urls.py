from django.conf.urls.defaults import patterns, url
from requestexample.views import RequestExampleView, EchoRequestContentView
from examples.views import MockView


urlpatterns = patterns('',
    url(r'^$', RequestExampleView.as_view(), name='request-example'),
    url(r'^content$', MockView.as_view(view_class=EchoRequestContentView), name='request-content'),
)
