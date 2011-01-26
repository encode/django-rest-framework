from django.conf.urls.defaults import patterns, include
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
<<<<<<< local
    (r'^blog-post-api/', include('blogpost.urls')),
    (r'^object-store-api/', include('objectstore.urls')),
    (r'^pygments-api/', include('pygments_api.urls')),
=======
    (r'pygments-example/', include('pygmentsapi.urls')),
    (r'^blog-post-example/', include('blogpost.urls')),
    (r'^object-store-example/', include('objectstore.urls')),
>>>>>>> other
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),
)
