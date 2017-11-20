"""
Login and logout views for the browsable API.

Add these to your root URLconf if you're using the browsable API and
your API requires authentication:

    urlpatterns = [
        ...
        url(r'^auth/', include('rest_framework.urls'))
    ]

You should make sure your authentication settings include `SessionAuthentication`.
"""
from __future__ import unicode_literals

import django
from django.conf.urls import url
from django.contrib.auth import views

if django.VERSION < (1, 11):
    login = views.login
    login_kwargs = {'template_name': 'rest_framework/login.html'}
    logout = views.logout
else:
    login = views.LoginView.as_view(template_name='rest_framework/login.html')
    login_kwargs = {}
    logout = views.LogoutView.as_view()


app_name = 'rest_framework'
urlpatterns = [
    url(r'^login/$', login, login_kwargs, name='login'),
    url(r'^logout/$', logout, name='logout'),
]
