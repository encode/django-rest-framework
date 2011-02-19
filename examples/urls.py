from django.conf.urls.defaults import patterns, include, url
from sandbox.views import Sandbox

urlpatterns = patterns('djangorestframework.views',
    (r'robots.txt', 'deny_robots'),
    (r'favicon.ico', 'favicon'),

    (r'^$', Sandbox.as_view()),

    (r'^resource-example/', include('resourceexample.urls')),
    (r'^model-resource-example/', include('modelresourceexample.urls')),
    (r'^mixin/', include('mixin.urls')),
    (r'^object-store/', include('objectstore.urls')),
    (r'^pygments/', include('pygments_api.urls')),
    (r'^blog-post/', include('blogpost.urls')),

    (r'^accounts/login/$', 'api_login'),
    (r'^accounts/logout/$', 'api_logout'),
)
