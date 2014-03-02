from django.test import TestCase
from rest_framework import serializers


class EmptySerializerTestCase(TestCase):
    def test_empty_serializer(self):
        class FooBarSerializer(serializers.Serializer):
            foo = serializers.IntegerField()
            bar = serializers.SerializerMethodField('get_bar')

            def get_bar(self, obj):
                return 'bar'

        serializer = FooBarSerializer()
        self.assertEquals(serializer.data, {'foo': 0})
