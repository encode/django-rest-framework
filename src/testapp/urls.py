from django.conf.urls.defaults import patterns
from testapp.views import ReadOnlyResource, MirroringWriteResource


urlpatterns = patterns('',
    (r'^read-only$', ReadOnlyResource),
    (r'^mirroring-write$', MirroringWriteResource),
)
