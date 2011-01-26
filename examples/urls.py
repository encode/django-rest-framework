from django.conf.urls.defaults import patterns, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'pygments-example/', include('pygmentsapi.urls')),
    (r'^blog-post-example/', include('blogpost.urls')),
    (r'^object-store-example/', include('objectstore.urls')),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)
