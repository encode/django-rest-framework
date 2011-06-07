from django.conf.urls.defaults import patterns, url
from resourceexample.views import ExampleView, AnotherExampleView

urlpatterns = patterns('',
    url(r'^$',                 ExampleView.as_view(), name='example-resource'),
    url(r'^(?P<num>[0-9]+)/$', AnotherExampleView.as_view(), name='another-example'),
)
