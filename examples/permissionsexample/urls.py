from django.conf.urls.defaults import patterns, url
from permissionsexample.views import ThrottlingExampleView

urlpatterns = patterns('',
    url(r'^$',                 ThrottlingExampleView.as_view(), name='throttled-resource'),
)
