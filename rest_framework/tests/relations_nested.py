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
        model = ForeignKeySource


class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    sources = ForeignKeySourceSerializer()

    class Meta:
        model = ForeignKeyTarget


class ReverseForeignKeyTests(TestCase):
    def setUp(self):
        target = ForeignKeyTarget(name='target-1')
        target.save()
        new_target = ForeignKeyTarget(name='target-2')
        new_target.save()
        for idx in range(1, 4):
            source = ForeignKeySource(name='source-%d' % idx, target=target)
            source.save()

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
