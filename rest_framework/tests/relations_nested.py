from django.db import models
from django.test import TestCase
from rest_framework import serializers


# ForeignKey

class ForeignKeyTarget(models.Model):
    name = models.CharField(max_length=100)


class ForeignKeySource(models.Model):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, related_name='sources')


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = ForeignKeySource


class FlatForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource


class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    sources = FlatForeignKeySourceSerializer()

    class Meta:
        model = ForeignKeyTarget


# Nullable ForeignKey

class NullableForeignKeySource(models.Model):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, null=True, blank=True,
                               related_name='nullable_sources')


class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = NullableForeignKeySource


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
        serializer = ForeignKeySourceSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': {'id': 1, 'name': u'target-1'}},
            {'id': 2, 'name': u'source-2', 'target': {'id': 1, 'name': u'target-1'}},
            {'id': 3, 'name': u'source-3', 'target': {'id': 1, 'name': u'target-1'}},
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'target-1', 'sources': [
                {'id': 1, 'name': u'source-1', 'target': 1},
                {'id': 2, 'name': u'source-2', 'target': 1},
                {'id': 3, 'name': u'source-3', 'target': 1},
            ]},
            {'id': 2, 'name': u'target-2', 'sources': [
            ]}
        ]
        self.assertEquals(serializer.data, expected)


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
        serializer = NullableForeignKeySourceSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': {'id': 1, 'name': u'target-1'}},
            {'id': 2, 'name': u'source-2', 'target': {'id': 1, 'name': u'target-1'}},
            {'id': 3, 'name': u'source-3', 'target': None},
        ]
        self.assertEquals(serializer.data, expected)
