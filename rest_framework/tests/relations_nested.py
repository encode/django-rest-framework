from __future__ import unicode_literals
from django.db import models
from django.test import TestCase
from rest_framework import serializers


class OneToOneTarget(models.Model):
    name = models.CharField(max_length=100)


class OneToOneTargetSource(models.Model):
    name = models.CharField(max_length=100)
    target = models.OneToOneField(OneToOneTarget, null=True, blank=True,
                                  related_name='target_source')


class OneToOneSource(models.Model):
    name = models.CharField(max_length=100)
    target_source = models.OneToOneField(OneToOneTargetSource, related_name='source')


class OneToOneSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneToOneSource
        exclude = ('target_source', )


class OneToOneTargetSourceSerializer(serializers.ModelSerializer):
    source = OneToOneSourceSerializer()

    class Meta:
        model = OneToOneTargetSource
        exclude = ('target', )


class OneToOneTargetSerializer(serializers.ModelSerializer):
    target_source = OneToOneTargetSourceSerializer()

    class Meta:
        model = OneToOneTarget


class OneToManyTarget(models.Model):
    name = models.CharField(max_length=100)


class OneToManyTargetSource(models.Model):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(OneToManyTarget,
                               related_name='target_sources')


class OneToManySource(models.Model):
    name = models.CharField(max_length=100)
    target_source = models.ForeignKey(OneToManyTargetSource,
                                      related_name='sources')


class OneToManySource(models.Model):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(OneToManyTarget,
                               related_name='sources')


class OneToManySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneToManySource
        exclude = ('target_source', )


class OneToManyTargetSourceSerializer(serializers.ModelSerializer):
    sources = OneToManySourceSerializer(many=True)

    class Meta:
        model = OneToManyTargetSource
        exclude = ('target', )


class OneToManyTargetSerializer(serializers.ModelSerializer):
    target_sources = OneToManyTargetSourceSerializer(many=True)

    class Meta:
        model = OneToManyTarget


class NestedOneToOneTests(TestCase):
    def setUp(self):
        for idx in range(1, 4):
            target = OneToOneTarget(name='target-%d' % idx)
            target.save()
            target_source = OneToOneTargetSource(name='target-source-%d' % idx, target=target)
            target_source.save()
            source = OneToOneSource(name='source-%d' % idx, target_source=target_source)
            source.save()

    def test_one_to_one_retrieve(self):
        queryset = OneToOneTarget.objects.all()
        serializer = OneToOneTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': 'target-1', 'target_source': {'id': 1, 'name': 'target-source-1', 'source': {'id': 1, 'name': 'source-1'}}},
            {'id': 2, 'name': 'target-2', 'target_source': {'id': 2, 'name': 'target-source-2', 'source': {'id': 2, 'name': 'source-2'}}},
            {'id': 3, 'name': 'target-3', 'target_source': {'id': 3, 'name': 'target-source-3', 'source': {'id': 3, 'name': 'source-3'}}}
        ]
        self.assertEqual(serializer.data, expected)

    def test_one_to_one_create(self):
        data = {'id': 4, 'name': 'target-4', 'target_source': {'id': 4, 'name': 'target-source-4', 'source': {'id': 4, 'name': 'source-4'}}}
        serializer = OneToOneTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'target-4')

        # Ensure (target 4, target_source 4, source 4) are added, and
        # everything else is as expected.
        queryset = OneToOneTarget.objects.all()
        serializer = OneToOneTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': 'target-1', 'target_source': {'id': 1, 'name': 'target-source-1', 'source': {'id': 1, 'name': 'source-1'}}},
            {'id': 2, 'name': 'target-2', 'target_source': {'id': 2, 'name': 'target-source-2', 'source': {'id': 2, 'name': 'source-2'}}},
            {'id': 3, 'name': 'target-3', 'target_source': {'id': 3, 'name': 'target-source-3', 'source': {'id': 3, 'name': 'source-3'}}},
            {'id': 4, 'name': 'target-4', 'target_source': {'id': 4, 'name': 'target-source-4', 'source': {'id': 4, 'name': 'source-4'}}}
        ]
        self.assertEqual(serializer.data, expected)

    def test_one_to_one_create_with_invalid_data(self):
        data = {'id': 4, 'name': 'target-4', 'target_source': {'id': 4, 'name': 'target-source-4', 'source': {'id': 4}}}
        serializer = OneToOneTargetSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'target_source': [{'source': [{'name': ['This field is required.']}]}]})

    def test_one_to_one_update(self):
        data = {'id': 3, 'name': 'target-3-updated', 'target_source': {'id': 3, 'name': 'target-source-3-updated', 'source': {'id': 3, 'name': 'source-3-updated'}}}
        instance = OneToOneTarget.objects.get(pk=3)
        serializer = OneToOneTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'target-3-updated')

        # Ensure (target 3, target_source 3, source 3) are updated,
        # and everything else is as expected.
        queryset = OneToOneTarget.objects.all()
        serializer = OneToOneTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': 'target-1', 'target_source': {'id': 1, 'name': 'target-source-1', 'source': {'id': 1, 'name': 'source-1'}}},
            {'id': 2, 'name': 'target-2', 'target_source': {'id': 2, 'name': 'target-source-2', 'source': {'id': 2, 'name': 'source-2'}}},
            {'id': 3, 'name': 'target-3-updated', 'target_source': {'id': 3, 'name': 'target-source-3-updated', 'source': {'id': 3, 'name': 'source-3-updated'}}}
        ]
        self.assertEqual(serializer.data, expected)

    def test_one_to_one_delete(self):
        data = {'id': 3, 'name': 'target-3', 'target_source': None}
        instance = OneToOneTarget.objects.get(pk=3)
        serializer = OneToOneTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()

        # Ensure (target_source 3, source 3) are deleted,
        # and everything else is as expected.
        queryset = OneToOneTarget.objects.all()
        serializer = OneToOneTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': 'target-1', 'target_source': {'id': 1, 'name': 'target-source-1', 'source': {'id': 1, 'name': 'source-1'}}},
            {'id': 2, 'name': 'target-2', 'target_source': {'id': 2, 'name': 'target-source-2', 'source': {'id': 2, 'name': 'source-2'}}},
            {'id': 3, 'name': 'target-3', 'target_source': None}
        ]
        self.assertEqual(serializer.data, expected)


class NestedOneToManyTests(TestCase):
    def setUp(self):
        target = OneToManyTarget(name='target-1')
        target.save()
        target_source = OneToManyTargetSource(name='target-source-1', target=target)
        target_source.save()
        for idx in range(1, 4):
            source = OneToManySource(name='source-%d' % idx, target_source=target_source)
            source.save()

    def test_one_to_many_retrieve(self):
        queryset = OneToManyTarget.objects.all()
        serializer = OneToManyTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': 'target-1', 'target_sources': [{'id': 1, 'name': 'target-source-1', 'sources': [{'id': 1, 'name': 'source-1'}, {'id': 2, 'name': 'source-2'}, {'id': 3, 'name': 'source-3'}]}]}
        ]
        self.assertEquals(serializer.data, expected)

    def test_one_to_many_create(self):
        # Note the nonsensical source id given
        data = {'id': 2, 'name': 'target-2', 'target_sources': [{'id': 2, 'name': 'target-source-2', 'sources': [{'id': 2, 'name': 'source-4'}]}]}
        expected = {'id': 2, 'name': 'target-2', 'target_sources': [{'id': 2, 'name': 'target-source-2', 'sources': [{'id': 4, 'name': 'source-4'}]}]}
        serializer = OneToManyTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, expected)
        self.assertEqual(obj.name, 'target-2')

        # Ensure (target 4, target_source 4, source 4) are added, and
        # everything else is as expected.
        queryset = OneToManyTarget.objects.all()
        serializer = OneToManyTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': 'target-1', 'target_sources': [{'id': 1, 'name': 'target-source-1', 'sources': [{'id': 1, 'name': 'source-1'}, {'id': 2, 'name': 'source-2'}, {'id': 3, 'name': 'source-3'}]}]},
            {'id': 2, 'name': 'target-2', 'target_sources': [{'id': 2, 'name': 'target-source-2', 'sources': [{'id': 4, 'name': 'source-4'}]}]}
        ]
        self.assertEquals(serializer.data, expected)

    def test_one_to_many_update(self):
        data = {'id': 1, 'name': 'target-1-updated', 'target_sources': [{'id': 1, 'name': 'target-source-1-updated', 'sources': [{'id': 1, 'name': 'source-1-updated'}, {'id': 2, 'name': 'source-2'}, {'id': 3, 'name': 'source-3'}]}]}
        expected = {'id': 1, 'name': 'target-1-updated', 'target_sources': [{'id': 1, 'name': 'target-source-1-updated', 'sources': [{'id': 1, 'name': 'source-1-updated'}, {'id': 2, 'name': 'source-2'}, {'id': 3, 'name': 'source-3'}]}]}
        instance = OneToManyTarget.objects.get(pk=1)
        serializer = OneToManyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, expected)
        self.assertEqual(obj.name, 'target-1-updated')

        # Ensure (target 1, target_source 1, source 1) are updated,
        # and everything else is as expected.
        queryset = OneToManyTarget.objects.all()
        serializer = OneToManyTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': 'target-1-updated', 'target_sources': [{'id': 1, 'name': 'target-source-1-updated', 'sources': [{'id': 1, 'name': 'source-1-updated'}, {'id': 2, 'name': 'source-2'}, {'id': 3, 'name': 'source-3'}]}]}
            ]
        self.assertEquals(serializer.data, expected)

    def test_one_to_many_delete(self):
        data = {'id': 1, 'name': 'target-1', 'target_sources': [{'id': 1, 'name': 'target-source-1', 'sources': [{'id': 2, 'name': 'source-2'}]}]}
        instance = OneToManyTarget.objects.get(pk=1)
        serializer = OneToManyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()

        # Ensure target_source 1 is deleted, and everything else is as
        # expected.
        queryset = OneToManyTarget.objects.all()
        serializer = OneToManyTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': 'target-1', 'target_sources': [{'id': 1, 'name': 'target-source-1', 'sources': [{'id': 2, 'name': 'source-2'}]}]}
            ]
        self.assertEquals(serializer.data, expected)
