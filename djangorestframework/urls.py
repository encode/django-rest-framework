"""
Login and logout views for the browseable API.

Add these to your root URLconf if you're using the browseable API and
your API requires authentication.

The urls must be namespaced as 'djangorestframework', and you should make sure
your authentication settings include `SessionAuthentication`.

    urlpatterns = patterns('',
        ...
        url(r'^auth', include('djangorestframework.urls', namespace='djangorestframework'))
    )
"""
from django.conf.urls.defaults import patterns, url


template_name = {'template_name': 'djangorestframework/login.html'}

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', template_name, name='login'),
    url(r'^logout/$', 'logout', template_name, name='logout'),
)
