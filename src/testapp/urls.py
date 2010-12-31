from django.conf.urls.defaults import patterns

urlpatterns = patterns('testapp.views',
    (r'^$', 'RootResource'),
    (r'^read-only$', 'ReadOnlyResource'),
    (r'^write-only$', 'WriteOnlyResource'),
    (r'^read-write$', 'ReadWriteResource'),
)
