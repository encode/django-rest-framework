from django.conf.urls.defaults import patterns

urlpatterns = patterns('djangorestframework.utils.staticviews',
    (r'^accounts/login/$', 'api_login'),
    (r'^accounts/logout/$', 'api_logout'),
)
