from django.conf.urls.defaults import patterns, url
from resourceexample.views import ExampleResource, AnotherExampleResource

urlpatterns = patterns('',
    url(r'^$',                 ExampleResource.as_view(), name='example-resource'),
    url(r'^(?P<num>[0-9]+)/$', AnotherExampleResource.as_view(), name='another-example-resource'),
)
