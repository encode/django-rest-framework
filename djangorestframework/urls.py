from django.conf.urls.defaults import patterns, url


template_name = {'template_name': 'djangorestframework/login.html'}

urlpatterns = patterns('django.contrib.auth.views',
    url(r'^login/$', 'login', template_name, name='login'),
    url(r'^logout/$', 'logout', template_name, name='logout'),
)
