from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('modelresourceexample.views',
    url(r'^$',          'MyModelRootResource'),
    url(r'^([0-9]+)/$', 'MyModelResource'),
)
