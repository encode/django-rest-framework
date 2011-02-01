from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('resourceexample.views',
    url(r'^$',                 'ExampleResource'),
    url(r'^(?P<num>[0-9]+)/$', 'AnotherExampleResource'),
)
