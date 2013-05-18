from __future__ import unicode_literals
from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import ForeignKeyTarget, ForeignKeySource, NullableForeignKeySource, OneToOneTarget, NullableOneToOneSource


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = ('id', 'name', 'target')
        depth = 1


class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeyTarget
        fields = ('id', 'name', 'sources')
        depth = 1


class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NullableForeignKeySource
        fields = ('id', 'name', 'target')
        depth = 1


class NullableOneToOneTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneToOneTarget
        fields = ('id', 'name', 'nullable_source')
        depth = 1


class ReverseForeignKeyTests(TestCase):
    def setUp(self):
        target = ForeignKeyTarget(name='target-1')
        target.save()
        new_target = ForeignKeyTarget(name='target-2')
        new_target.save()
        for idx in range(1, 4):
            source = ForeignKeySource(name='source-%d' % idx, target=target)
            source.save()

    def test_foreign_key_retrieve(self):
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': {'id': 1, 'name': 'target-1'}},
            {'id': 2, 'name': 'source-2', 'target': {'id': 1, 'name': 'target-1'}},
            {'id': 3, 'name': 'source-3', 'target': {'id': 1, 'name': 'target-1'}},
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [
                {'id': 1, 'name': 'source-1', 'target': 1},
                {'id': 2, 'name': 'source-2', 'target': 1},
                {'id': 3, 'name': 'source-3', 'target': 1},
            ]},
            {'id': 2, 'name': 'target-2', 'sources': [
            ]}
        ]
        self.assertEqual(serializer.data, expected)


class NestedNullableForeignKeyTests(TestCase):
    def setUp(self):
        target = ForeignKeyTarget(name='target-1')
        target.save()
        for idx in range(1, 4):
            if idx == 3:
                target = None
            source = NullableForeignKeySource(name='source-%d' % idx, target=target)
            source.save()

    def test_foreign_key_retrieve_with_null(self):
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': {'id': 1, 'name': 'target-1'}},
            {'id': 2, 'name': 'source-2', 'target': {'id': 1, 'name': 'target-1'}},
            {'id': 3, 'name': 'source-3', 'target': None},
        ]
        self.assertEqual(serializer.data, expected)


class NestedNullableOneToOneTests(TestCase):
    def setUp(self):
        target = OneToOneTarget(name='target-1')
        target.save()
        new_target = OneToOneTarget(name='target-2')
        new_target.save()
        source = NullableOneToOneSource(name='source-1', target=target)
        source.save()

    def test_reverse_foreign_key_retrieve_with_null(self):
        queryset = OneToOneTarget.objects.all()
        serializer = NullableOneToOneTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'nullable_source': {'id': 1, 'name': 'source-1', 'target': 1}},
            {'id': 2, 'name': 'target-2', 'nullable_source': None},
        ]
        self.assertEqual(serializer.data, expected)
