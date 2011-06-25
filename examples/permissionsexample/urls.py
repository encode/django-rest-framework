from django.conf.urls.defaults import patterns, url
from permissionsexample.views import PermissionsExampleView, ThrottlingExampleView, LoggedinView

urlpatterns = patterns('',
    url(r'^$', PermissionsExampleView.as_view(), name='permissions-example'),
    url(r'^throttling$', ThrottlingExampleView.as_view(), name='throttled-resource'),
    url(r'^loggedin$', LoggedinView.as_view(), name='loggedin-resource'),
)
