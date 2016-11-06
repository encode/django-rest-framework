from django.conf.urls import url
from django.db import models
from django.test import TestCase, override_settings

from rest_framework import serializers
from rest_framework.renderers import JSONRenderer
from rest_framework.templatetags.rest_framework import format_value

str_called = False


class Example(models.Model):
    text = models.CharField(max_length=100)

    def __str__(self):
        global str_called
        str_called = True
        return 'An example'


class ExampleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Example
        fields = ('url', 'id', 'text')


def dummy_view(request):
    pass


urlpatterns = [
    url(r'^example/(?P<pk>[0-9]+)/$', dummy_view, name='example-detail'),
]


@override_settings(ROOT_URLCONF='tests.test_lazy_hyperlinks')
class TestLazyHyperlinkNames(TestCase):
    def setUp(self):
        self.example = Example.objects.create(text='foo')

    def test_lazy_hyperlink_names(self):
        global str_called
        context = {'request': None}
        serializer = ExampleSerializer(self.example, context=context)
        JSONRenderer().render(serializer.data)
        assert not str_called
        hyperlink_string = format_value(serializer.data['url'])
        assert hyperlink_string == '<a href=/example/1/>An example</a>'
        assert str_called
