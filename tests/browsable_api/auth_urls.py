from __future__ import unicode_literals
from django.conf.urls import patterns, url, include
from rest_framework import routers

from .views import MockView, FooViewSet, BarViewSet

router = routers.SimpleRouter()
router.register(r'foo', FooViewSet)
router.register(r'bar', BarViewSet)

urlpatterns = patterns(
    '',
    (r'^$', MockView.as_view()),
    url(r'^', include(router.urls)),
    url(r'^bar/(?P<pk>\d+)/$', BarViewSet, name='bar-list'),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
)
