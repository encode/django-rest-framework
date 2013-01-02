from django.db import models
from django.test import TestCase
from rest_framework import serializers


# ForeignKey

class ForeignKeyTarget(models.Model):
    name = models.CharField(max_length=100)


class ForeignKeyTargetSource(models.Model):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, related_name='target_sources')


class ForeignKeySource(models.Model):
    name = models.CharField(max_length=100)    
    target = models.ForeignKey(ForeignKeyTarget, related_name='sources')
    target_source = models.ForeignKey(ForeignKeyTargetSource, related_name='sources')

    class Meta:
        app_label = 'tests'
    
class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = ForeignKeySource


class FlatForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource


class FlatForeignKeyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeyTarget


class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    sources = FlatForeignKeySourceSerializer()

    class Meta:
        model = ForeignKeyTarget


class ForeignKeyTargetSourceSerializer1(serializers.ModelSerializer):
    sources = FlatForeignKeySourceSerializer()

    class Meta:
        model = ForeignKeyTargetSource


class ForeignKeyTargetSourceSerializer2(serializers.ModelSerializer):
    target = FlatForeignKeyTargetSerializer()

    class Meta:
        model = ForeignKeyTargetSource


class ReverseReverseSerializer(serializers.ModelSerializer):
    target_sources = ForeignKeyTargetSourceSerializer1()

    class Meta:
        model = ForeignKeyTarget        


class ReverseForwardSerializer(serializers.ModelSerializer):
    sources = ForeignKeySourceSerializer()

    class Meta:
        model = ForeignKeyTargetSource


class ForwardForwardSerializer(serializers.ModelSerializer):
    target_sources = ForeignKeyTargetSourceSerializer2()

    class Meta:
        model = ForeignKeySource


class ForwardReverseSerializer(serializers.ModelSerializer):
    target = ForeignKeyTargetSerializer()

    class Meta:
        model = ForeignKeyTargetSource
    

# Nullable ForeignKey

class NullableForeignKeySource(models.Model):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(ForeignKeyTarget, null=True, blank=True,
                               related_name='nullable_sources')


class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = NullableForeignKeySource


class NestedForeignKeyTests(TestCase):
    def setUp(self):
        target = ForeignKeyTarget(name='target-1')
        target.save()
        new_target = ForeignKeyTarget(name='target-2')
        new_target.save()
        target_source = ForeignKeyTargetSource(name='target-source-1', target=target)
        target_source.save()
        new_target_source = ForeignKeyTargetSource(name='target-source-2', target=target)
        new_target_source.save()
        for idx in range(1, 4):
            import pdb
            pdb.set_trace()
            source = ForeignKeySource(name='source-%d' % idx, target=target, target_source=target_source)
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

    def test_reverse_foreign_key_create(self):
        target = ForeignKeyTarget.objects.get(name='target-2')
        # The value for target here should be ignored
        data = {'sources': [{'name': u'source-4', 'target': 1},
                            {'name': u'source-5', 'target': 1}],
                'name': u'target-2'
                }
        expected = {'sources': [{'id': 4, 'name': u'source-4', 'target': 2},
                                {'id': 5, 'name': u'source-5', 'target': 2}],
                    'id': 2, 'name': u'target-2'
                    }
        serializer = ForeignKeyTargetSerializer(target, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        # Ensure target 2 has new source and everything else is as expected
        target = ForeignKeyTarget.objects.get(name='target-2')
        serializer = ForeignKeyTargetSerializer(target)
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
