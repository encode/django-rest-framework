from __future__ import unicode_literals

from django.conf.urls import url

from .views import MockView

urlpatterns = [
    url(r'^$', MockView.as_view()),
]
