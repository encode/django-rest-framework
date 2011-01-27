from django.conf.urls.defaults import patterns, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'pygments-example/', include('pygments_api.urls')),
    (r'^blog-post-example/', include('blogpost.urls')),
    (r'^object-store-example/', include('objectstore.urls')),
    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)
