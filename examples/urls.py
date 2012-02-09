from django.conf.urls.defaults import patterns, include
from sandbox.views import Sandbox
try:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
except ImportError:  # Django <= 1.2
    from staticfiles.urls import staticfiles_urlpatterns


urlpatterns = patterns('',
    (r'^$', Sandbox.as_view()),
    (r'^resource-example/', include('resourceexample.urls')),
    (r'^model-resource-example/', include('modelresourceexample.urls')),
    (r'^mixin/', include('mixin.urls')),
    (r'^object-store/', include('objectstore.urls')),
    (r'^pygments/', include('pygments_api.urls')),
    (r'^blog-post/', include('blogpost.urls')),
    (r'^permissions-example/', include('permissionsexample.urls')),

    (r'^', include('djangorestframework.urls')),
)

urlpatterns += staticfiles_urlpatterns()
