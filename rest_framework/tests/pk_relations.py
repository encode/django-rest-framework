from django.db import models
from django.test import TestCase
from rest_framework import serializers


# ManyToMany

class ManyToManyTarget(models.Model):
    name = models.CharField(max_length=100)


class ManyToManySource(models.Model):
    name = models.CharField(max_length=100)
    targets = models.ManyToManyField(ManyToManyTarget, related_name='sources')


class ManyToManyTargetSerializer(serializers.ModelSerializer):
    sources = serializers.ManyPrimaryKeyRelatedField()

    class Meta:
        model = ManyToManyTarget


class ManyToManySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManySource


# ForeignKey

class ForeignKeyTarget(models.Model):
    name = models.CharField(max_length=100)


class ForeignKeySource(models.Model):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, related_name='sources')


class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    sources = serializers.ManyPrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ForeignKeyTarget


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource


# TODO: Add test that .data cannot be accessed prior to .is_valid

class PrimaryKeyManyToManyTests(TestCase):
    def setUp(self):
        for idx in range(1, 4):
            target = ManyToManyTarget(name='target-%d' % idx)
            target.save()
            source = ManyToManySource(name='source-%d' % idx)
            source.save()
            for target in ManyToManyTarget.objects.all():
                source.targets.add(target)

    def test_many_to_many_retrieve(self):
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset)
        expected = [
                {'id': 1, 'name': u'source-1', 'targets': [1]},
                {'id': 2, 'name': u'source-2', 'targets': [1, 2]},
                {'id': 3, 'name': u'source-3', 'targets': [1, 2, 3]}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_many_to_many_retrieve(self):
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': u'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': u'target-3', 'sources': [3]}
        ]
        self.assertEquals(serializer.data, expected)

    def test_many_to_many_update(self):
        data = {'id': 1, 'name': u'source-1', 'targets': [1, 2, 3]}
        instance = ManyToManySource.objects.get(pk=1)
        serializer = ManyToManySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset)
        expected = [
                {'id': 1, 'name': u'source-1', 'targets': [1, 2, 3]},
                {'id': 2, 'name': u'source-2', 'targets': [1, 2]},
                {'id': 3, 'name': u'source-3', 'targets': [1, 2, 3]}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_many_to_many_update(self):
        data = {'id': 1, 'name': u'target-1', 'sources': [1]}
        instance = ManyToManyTarget.objects.get(pk=1)
        serializer = ManyToManyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, data)
        serializer.save()

        # Ensure target 1 is updated, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'target-1', 'sources': [1]},
            {'id': 2, 'name': u'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': u'target-3', 'sources': [3]}
        ]
        self.assertEquals(serializer.data, expected)


class PrimaryKeyForeignKeyTests(TestCase):
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
            {'id': 1, 'name': u'source-1', 'target': 1},
            {'id': 2, 'name': u'source-2', 'target': 1},
            {'id': 3, 'name': u'source-3', 'target': 1}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': u'target-2', 'sources': []},
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_update(self):
        data = {'id': 1, 'name': u'source-1', 'target': 2}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, data)
        serializer.save()

        # # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': 2},
            {'id': 2, 'name': u'source-2', 'target': 1},
            {'id': 3, 'name': u'source-3', 'target': 1}
        ]
        self.assertEquals(serializer.data, expected)

    # reverse foreign keys MUST be read_only
    # In the general case they do not provide .remove() or .clear()
    # and cannot be arbitrarily set.

    # def test_reverse_foreign_key_update(self):
    #     data = {'id': 1, 'name': u'target-1', 'sources': [1]}
    #     instance = ForeignKeyTarget.objects.get(pk=1)
    #     serializer = ForeignKeyTargetSerializer(instance, data=data)
    #     self.assertTrue(serializer.is_valid())
    #     self.assertEquals(serializer.data, data)
    #     serializer.save()

    #     # Ensure target 1 is updated, and everything else is as expected
    #     queryset = ForeignKeyTarget.objects.all()
    #     serializer = ForeignKeyTargetSerializer(queryset)
    #     expected = [
    #         {'id': 1, 'name': u'target-1', 'sources': [1]},
    #         {'id': 2, 'name': u'target-2', 'sources': []},
    #     ]
    #     self.assertEquals(serializer.data, expected)
