from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('simpleexample.views',
    url(r'^$',         'MyModelRootResource'),
    url(r'^([0-9]+)/$', 'MyModelResource'),
)
