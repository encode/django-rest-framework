"""
Login and logout views for the browsable API.

Add these to your root URLconf if you're using the browsable API and
your API requires authentication.

The urls must be namespaced as 'rest_framework', and you should make sure
your authentication settings include `SessionAuthentication`.

    urlpatterns = patterns('',
        ...
        url(r'^auth', include('rest_framework.urls', namespace='rest_framework'))
    )
"""
from __future__ import unicode_literals
from rest_framework.compat import patterns, url


template_name = {'template_name': 'rest_framework/login.html'}

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', template_name, name='login'),
    url(r'^logout/$', 'logout', template_name, name='logout'),
)
