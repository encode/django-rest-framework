from __future__ import unicode_literals
from django.conf.urls import patterns

from .views import MockView

urlpatterns = patterns(
    '',
    (r'^$', MockView.as_view()),
)
