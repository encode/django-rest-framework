"""
Login and logout views for the browsable API.

Add these to your root URLconf if you're using the browsable API and
your API requires authentication:

    urlpatterns = patterns('',
        ...
        url(r'^auth/', include('rest_framework.urls', namespace='rest_framework'))
    )

The urls must be namespaced as 'rest_framework', and you should make sure
your authentication settings include `SessionAuthentication`.
"""
from __future__ import unicode_literals
from django.conf.urls import patterns, url
from django.contrib.auth import views


template_name = {'template_name': 'rest_framework/login.html'}

urlpatterns = patterns(
    '',
    url(r'^login/$', views.login, template_name, name='login'),
    url(r'^logout/$', views.logout, template_name, name='logout')
)
