from django.db import models
from django.test import TestCase
from rest_framework import serializers


class Target(models.Model):
    name = models.CharField(max_length=100)


class Source(models.Model):
    name = models.CharField(max_length=100)
    targets = models.ManyToManyField(Target, related_name='sources')


class TargetSerializer(serializers.ModelSerializer):
    sources = serializers.ManyPrimaryKeyRelatedField()

    class Meta:
        fields = ('id', 'name', 'sources')
        model = Target


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source


# TODO: Add test that .data cannot be accessed prior to .is_valid

class PrimaryKeyManyToManyTests(TestCase):
    def setUp(self):
        for idx in range(1, 4):
            target = Target(name='target-%d' % idx)
            target.save()
            source = Source(name='source-%d' % idx)
            source.save()
            for target in Target.objects.all():
                source.targets.add(target)

    def test_many_to_many_retrieve(self):
        serializer = SourceSerializer(instance=Source.objects.all())
        expected = [
                {'id': 1, 'name': u'source-1', 'targets': [1]},
                {'id': 2, 'name': u'source-2', 'targets': [1, 2]},
                {'id': 3, 'name': u'source-3', 'targets': [1, 2, 3]}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_many_to_many_retrieve(self):
        serializer = TargetSerializer(instance=Target.objects.all())
        expected = [
            {'id': 1, 'name': u'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': u'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': u'target-3', 'sources': [3]}
        ]
        self.assertEquals(serializer.data, expected)

    def test_many_to_many_update(self):
        data = {'id': 1, 'name': u'source-1', 'targets': [1, 2, 3]}
        serializer = SourceSerializer(data, instance=Source.objects.get(pk=1))
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, data)

        # Ensure source 1 is updated, and everything else is as expected
        serializer = SourceSerializer(instance=Source.objects.all())
        expected = [
                {'id': 1, 'name': u'source-1', 'targets': [1, 2, 3]},
                {'id': 2, 'name': u'source-2', 'targets': [1, 2]},
                {'id': 3, 'name': u'source-3', 'targets': [1, 2, 3]}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_many_to_many_update(self):
        data = {'id': 1, 'name': u'target-0', 'sources': [1]}
        serializer = TargetSerializer(data, instance=Target.objects.get(pk=1))
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, data)

        # Ensure target 1 is updated, and everything else is as expected
        serializer = TargetSerializer(instance=Target.objects.all())
        expected = [
            {'id': 1, 'name': u'target-1', 'sources': [1]},
            {'id': 2, 'name': u'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': u'target-3', 'sources': [3]}
        ]
        self.assertEquals(serializer.data, expected)
