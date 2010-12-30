from django.conf.urls.defaults import patterns

urlpatterns = patterns('testapp.views',
    (r'^$', 'RootResource'),
    (r'^read-only$', 'ReadOnlyResource'),
    (r'^mirroring-write$', 'MirroringWriteResource'),
)
