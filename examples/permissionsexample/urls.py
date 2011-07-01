from django.conf.urls.defaults import patterns, url
from permissionsexample.views import PermissionsExampleView, ThrottlingExampleView, LoggedInExampleView

urlpatterns = patterns('',
    url(r'^$', PermissionsExampleView.as_view(), name='permissions-example'),
    url(r'^throttling$', ThrottlingExampleView.as_view(), name='throttled-resource'),
    url(r'^loggedin$', LoggedInExampleView.as_view(), name='loggedin-resource'),
)
