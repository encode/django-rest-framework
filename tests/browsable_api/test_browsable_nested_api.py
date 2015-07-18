from __future__ import unicode_literals

from django.conf.urls import url
from django.test import TestCase
from django.test.utils import override_settings

from rest_framework import serializers
from rest_framework.generics import ListCreateAPIView
from rest_framework.renderers import BrowsableAPIRenderer


class NestedSerializer(serializers.Serializer):
    one = serializers.IntegerField(max_value=10)
    two = serializers.IntegerField(max_value=10)


class TestNestedSerializerSerializer(serializers.Serializer):
    nested = NestedSerializer()


class NestedSerializersView(ListCreateAPIView):
    renderer_classes = (BrowsableAPIRenderer, )
    serializer_class = TestNestedSerializerSerializer
    queryset = [{'nested': {'one': 1, 'two': 2}}]


urlpatterns = [
    url(r'^api/$', NestedSerializersView.as_view(), name='api'),
]


class DropdownWithAuthTests(TestCase):
    """Tests correct dropdown behaviour with Auth views enabled."""

    @override_settings(ROOT_URLCONF='tests.browsable_api.test_browsable_nested_api')
    def test_login(self):
        response = self.client.get('/api/')
        self.assertEqual(200, response.status_code)
        content = response.content.decode('utf-8')
        self.assertIn('form action="/api/"', content)
        self.assertIn('input name="nested.one"', content)
        self.assertIn('input name="nested.two"', content)
