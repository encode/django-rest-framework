from __future__ import unicode_literals

from django.test import TestCase, override_settings

from rest_framework import serializers


class ChildSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        # Not calling self.root

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value['root'] = self.root
        return value


class AnotherChildSerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self.root  # Calling self.root to ruin the cache

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value['root'] = self.root
        return value


class ParentSerializer(serializers.Serializer):
    children = ChildSerializer(many=True)
    other_children = AnotherChildSerializer(many=True)

    def __init__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        # Not calling self.root

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value['root'] = self.root
        return value


class RootSerializer(serializers.Serializer):
    parents = ParentSerializer(many=True)


class ListManyToManyTests(TestCase):
    def setUp(self):
        self.root = RootSerializer(data={
            'parents': [{
                'children': [{'name': 'child'}],
                'other_children': [{'name': 'child'}],
            }],
        })
        self.root.is_valid()

    def test_relative_hyperlinks(self):
        assert self.root.root == self.root
        assert self.root.validated_data['parents'][0]['root'] == self.root
        assert self.root.validated_data['parents'][0]['children'][0]['root'] == self.root
        assert self.root.validated_data['parents'][0]['other_children'][0]['root'] == self.root
