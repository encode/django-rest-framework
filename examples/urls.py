from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from sandbox.views import Sandbox

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

