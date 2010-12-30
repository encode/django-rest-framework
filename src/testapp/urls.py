from django.conf.urls.defaults import patterns

urlpatterns = patterns('testapp.views',
    (r'^$', 'RootResource'),
    (r'^read-only$', 'ReadOnlyResource'),
    (r'^write-only$', 'MirroringWriteResource'),
    (r'^read-write$', 'ReadWriteResource'),
)
