from django.db import models
from django.test import TestCase
from rest_framework import serializers


class OneToOneTarget(models.Model):
    name = models.CharField(max_length=100)


class OneToOneTargetSource(models.Model):
    name = models.CharField(max_length=100)
    target = models.OneToOneField(OneToOneTarget, related_name='target_source')


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
            {'id': 1, 'name': u'target-1', 'target_source': {'id': 1, 'name': u'target-source-1', 'source': {'id': 1, 'name': u'source-1'}}},
            {'id': 2, 'name': u'target-2', 'target_source': {'id': 2, 'name': u'target-source-2', 'source': {'id': 2, 'name': u'source-2'}}},
            {'id': 3, 'name': u'target-3', 'target_source': {'id': 3, 'name': u'target-source-3', 'source': {'id': 3, 'name': u'source-3'}}}            
        ]
        self.assertEquals(serializer.data, expected)
        

    def test_one_to_one_create(self):
        data = {'id': 4, 'name': u'target-4', 'target_source': {'id': 4, 'name': u'target-source-4', 'source': {'id': 4, 'name': u'source-4'}}}
        serializer = OneToOneTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'target-4')

        # Ensure (source 4, target 4) is added, and everything else is as expected
        queryset = OneToOneTarget.objects.all()
        serializer = OneToOneTargetSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'target-1', 'target_source': {'id': 1, 'name': u'target-source-1', 'source': {'id': 1, 'name': u'source-1'}}},
            {'id': 2, 'name': u'target-2', 'target_source': {'id': 2, 'name': u'target-source-2', 'source': {'id': 2, 'name': u'source-2'}}},
            {'id': 3, 'name': u'target-3', 'target_source': {'id': 3, 'name': u'target-source-3', 'source': {'id': 3, 'name': u'source-3'}}},
            {'id': 4, 'name': u'target-4', 'target_source': {'id': 4, 'name': u'target-source-4', 'source': {'id': 4, 'name': u'source-4'}}}
        ]
        self.assertEquals(serializer.data, expected)

    def test_one_to_one_create_with_invalid_data(self):
        data = {'id': 4, 'name': u'target-4', 'target_source': {'id': 4, 'name': u'target-source-4', 'source': {'id': 4}}}
        serializer = OneToOneTargetSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'target_source': [{'source': [{'name': [u'This field is required.']}]}]})
