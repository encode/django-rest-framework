# -*- coding: utf-8 -*-
# This is based on https://github.com/kevin-brown/django-rest-framework/compare/issue_1237.
from __future__ import unicode_literals

from django.test import TestCase
from rest_framework.compat import patterns, url
from rest_framework.generics import GenericAPIView
from rest_framework.renderers import BrowsableAPIRenderer
from rest_framework.response import Response
from rest_framework.serializers import Serializer, HyperlinkedRelatedField
from rest_framework.tests.models import Album


class TestSerializer(Serializer):
    field = HyperlinkedRelatedField(queryset=Album.objects, view_name="")


class TestView(GenericAPIView):
    renderer_classes = (BrowsableAPIRenderer, )
    serializer_class = TestSerializer

    def post(self, request, **kwargs):
        return Response("text")


urlpatterns = patterns('',
    url(r"^view/(?P<pk>\d+)$", TestView.as_view(), name="view"),
)


class FailingTestCase(TestCase):
    urls = 'rest_framework.tests.test_issue_1237'

    def test_issue_1237(self):
        album = Album(title="test")
        album.save()

        response = self.client.post("/view/{0}".format(album.pk))
        self.assertEqual(200, response.status_code)
