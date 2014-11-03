from __future__ import unicode_literals
from django.conf.urls import patterns

from .views import MockView, CreateOnlyView

urlpatterns = patterns(
    '',
    (r'^$', MockView.as_view()),
    (r'^create/$', CreateOnlyView.as_view()),
)
