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
from django.conf.urls import url
from django.contrib.auth import views

app_name = 'rest_framework'
urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(template_name='rest_framework/login.html'), name='login'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout'),
]
