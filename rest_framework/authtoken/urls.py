"""
Login view for token authentication.

Add this to your root URLconf if you're using token authentication
your API requires authentication.

You should make sure your authentication settings include
`TokenAuthentication`. 

    urlpatterns = patterns('',
        ...
        url(r'^auth-token/', 'rest_framework.authtoken.obtain_auth_token')
    )
"""

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('rest_framework.authtoken.views',
    url(r'^login/$', 'rest_framework.authtoken.views.obtain_auth_token', name='token_login'),
)
