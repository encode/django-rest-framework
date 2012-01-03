from django.conf.urls.defaults import patterns
from django.conf import settings

urlpatterns = patterns('djangorestframework.utils.staticviews',
    (r'robots.txt', 'deny_robots'),
    (r'^accounts/login/$', 'api_login'),
    (r'^accounts/logout/$', 'api_logout'),
)

# Only serve favicon in production because otherwise chrome users will pretty much
# permanantly have the django-rest-framework favicon whenever they navigate to
# 127.0.0.1:8000 or whatever, which gets annoying
if not settings.DEBUG:
    urlpatterns += patterns('djangorestframework.utils.staticviews',
        (r'favicon.ico', 'favicon'),
    )
