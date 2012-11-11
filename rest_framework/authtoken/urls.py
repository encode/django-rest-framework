"""
Login and logout views for token authentication.

Add these to your root URLconf if you're using token authentication
your API requires authentication.

The urls must be namespaced as 'rest_framework', and you should make sure
your authentication settings include `TokenAuthentication`.

    urlpatterns = patterns('',
        ...
        url(r'^auth-token', include('rest_framework.authtoken.urls', namespace='rest_framework'))
    )
"""
from django.conf.urls.defaults import patterns, url
from rest_framework.authtoken.views import AuthTokenLoginView, AuthTokenLogoutView

urlpatterns = patterns('rest_framework.authtoken.views',
    url(r'^login/$', AuthTokenLoginView.as_view(), name='token_login'),
    url(r'^logout/$', AuthTokenLogoutView.as_view(), name='token_logout'),
)
