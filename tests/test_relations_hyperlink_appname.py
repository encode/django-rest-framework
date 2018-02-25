from __future__ import unicode_literals

import pytest
from django.conf.urls import include, url
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase

from rest_framework import routers, serializers, viewsets
from rest_framework.test import APIRequestFactory, URLPatternsTestCase
from rest_framework.utils import json

factory = APIRequestFactory()
request = factory.get('/')  # Just to ensure we have a request in the serializer context


class Wine(models.Model):
    title = models.CharField(max_length=100)


class WineSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Wine
        fields = ('url', 'title')


class WineViewSet(viewsets.ModelViewSet):
    queryset = Wine.objects.all()
    serializer_class = WineSerializer


router = routers.DefaultRouter()
router.register(r'wines', WineViewSet)


class TestHyperlinkedRouterNoName(URLPatternsTestCase, TestCase):

    urlpatterns = [
        url(r'^api/', include(router.urls)),
    ]

    def test_no_name_works(self):
        w = Wine(title="Shiraz")
        w.save()

        response = self.client.get('/api/wines/')
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8')) == [{'title': 'Shiraz', 'url': 'http://testserver/api/wines/1/'}]


# Failing case with Django 2.0 and HyperlinkedModelSerializer
class TestHyperlinkedRouterFailsWithName(URLPatternsTestCase, TestCase):
    urlpatterns = [
        url(r'^api2/', include((router.urls, 'appname2'))),
    ]

    def test_hyperlink_fails(self):
        w = Wine(title="Shiraz")
        w.save()

        with pytest.raises(
                ImproperlyConfigured,
                message='Could not resolve URL for hyperlinked relationship using view '
                        'name "wine-detail". You may have failed to include the related model in '
                        'your API, or incorrectly configured the `lookup_field` attribute on this field.'):

            self.client.get('/api2/wines/')


router2 = routers.DefaultRouter(app_name='appname2')
router2.register(r'wines', WineViewSet)


class TestHyperlinkedRouterConfigured(URLPatternsTestCase, TestCase):
    urlpatterns = [
        url(r'^api2/', include((router2.urls, 'appname2'))),
    ]

    def test_regex_url_path_list(self):
        w = Wine(title="Shiraz")
        w.save()

        response = self.client.get('/api2/wines/')
        assert response.status_code == 200
        assert json.loads(response.content.decode('utf-8')) == [{'title': 'Shiraz', 'url': 'http://testserver/api2/wines/1/'}]
