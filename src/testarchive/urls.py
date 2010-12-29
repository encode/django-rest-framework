from django.conf.urls.defaults import patterns
from testarchive.views import RootResource


urlpatterns = patterns('',
    (r'^$', RootResource),
)
