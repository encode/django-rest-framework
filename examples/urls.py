from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from sandbox.views import Sandbox

urlpatterns = patterns('djangorestframework.views',
    (r'robots.txt', 'deny_robots'),

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

# Only serve favicon in production because otherwise chrome users will pretty much
# permanantly have the django-rest-framework favicon whenever they navigate to
# 127.0.0.1:8000 or whatever, which gets annoying
if not settings.DEBUG:
    urlpatterns += patterns('djangorestframework.views',
        (r'favicon.ico', 'favicon'),
    )
