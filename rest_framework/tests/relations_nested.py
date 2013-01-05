from django.db import models
from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import ForeignKeyTarget, ForeignKeySource, NullableForeignKeySource, NestedTarget, NestedTargetSource, NestedSource


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


class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        model = NullableForeignKeySource


class FlatNestedSourceSeriailizer(serializers.ModelSerializer):
    class Meta:
        model = NestedSource


class FlatNestedTargetSeriailizer(serializers.ModelSerializer):
    class Meta:
        model = NestedTarget


class ForwardNestedSourceSerializer(serializers.ModelSerializer):
    target = FlatNestedTargetSeriailizer()

    class Meta:
        model = NestedSource


class ReverseNestedTargetSerializer(serializers.ModelSerializer):
    sources = FlatNestedSourceSeriailizer()

    class Meta:
        model = NestedTarget


class ForwardNestedTargetSourceSerializer(serializers.ModelSerializer):
    target = FlatNestedTargetSeriailizer()

    class Meta:
        model = NestedTargetSource


class ReverseNestedTargetSourceSerializer(serializers.ModelSerializer):
    sources = FlatNestedSourceSeriailizer()

    class Meta:
        model = NestedTargetSource


class ForwardForwardSerializer(serializers.ModelSerializer):
    target_source = ForwardNestedTargetSourceSerializer()

    class Meta:
        model = NestedSource


class ReverseReverseSerializer(serializers.ModelSerializer):
    target_sources = ReverseNestedTargetSourceSerializer()

    class Meta:
        model = NestedTarget


class ForwardReverseSerializer(serializers.ModelSerializer):
    target = ReverseNestedTargetSerializer()

    class Meta:
        model = NestedTargetSource


class ReverseForwardSerializer(serializers.ModelSerializer):
    sources = ForwardNestedSourceSerializer()

    class Meta:
        model = NestedTargetSource


class DoublyNestedForeignKeyTests(TestCase):
    def setUp(self):
        target = NestedTarget(name='target-1')
        target.save()
        new_target = NestedTarget(name='target-2')
        new_target.save()
        target_source = NestedTargetSource(name='target-source-1', target=target)
        target_source.save()
        new_target_source = NestedTargetSource(name='target-source-2', target=new_target)
        new_target_source.save()
        for idx in range(1, 4):
            source = NestedSource(name='source-%d' % idx, target=target, target_source=target_source)
            source.save()
    
    def test_forward_forward_retrive(self):
        queryset = NestedSource.objects.all()
        serializer = ForwardForwardSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': 1, 'target_source': {'id': 1, 'name': u'target-source-1', 'target': {'id': 1, 'name': u'target-1'}}},
            {'id': 2, 'name': u'source-2', 'target': 1, 'target_source': {'id': 1, 'name': u'target-source-1', 'target': {'id': 1, 'name': u'target-1'}}},
            {'id': 3, 'name': u'source-3', 'target': 1, 'target_source': {'id': 1, 'name': u'target-source-1', 'target': {'id': 1, 'name': u'target-1'}}},
        ]
        self.assertEquals(serializer.data, expected)        

    def test_forward_reverse_retrive(self):
        queryset = NestedTargetSource.objects.all()
        serializer = ForwardReverseSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'target-source-1', 'target': {'id': 1, 'name': u'target-1', 'sources': [{'id': 1, 'name': u'source-1', 'target': 1, 'target_source': 1}, {'id': 2, 'name': u'source-2', 'target': 1, 'target_source': 1}, {'id': 3, 'name': u'source-3', 'target': 1, 'target_source': 1}]}},
            {'id': 2, 'name': u'target-source-2', 'target': {'id': 2, 'name': u'target-2', 'sources': []}}
            ]
        self.assertEquals(serializer.data, expected)        

    def test_reverse_reverse_retrive(self):
        queryset = NestedTarget.objects.all()
        serializer = ReverseReverseSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'target-1', 'target_sources': [{'id': 1, 'name': u'target-source-1', 'target': 1, 'sources': [{'id': 1, 'name': u'source-1', 'target': 1, 'target_source': 1}, {'id': 2, 'name': u'source-2', 'target': 1, 'target_source': 1}, {'id': 3, 'name': u'source-3', 'target': 1, 'target_source': 1}]}]},
            {'id': 2, 'name': u'target-2', 'target_sources': [{'id': 2, 'name': u'target-source-2', 'target': 2, 'sources': []}]}
        ]
        self.assertEquals(serializer.data, expected)        

    def test_reverse_forward_retrive(self):
        queryset = NestedTargetSource.objects.all()
        serializer = ReverseForwardSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'target-source-1', 'target': 1, 'sources': [{'id': 1, 'name': u'source-1', 'target': {'id': 1, 'name': u'target-1'}, 'target_source': 1}, {'id': 2, 'name': u'source-2', 'target': {'id': 1, 'name': u'target-1'}, 'target_source': 1}, {'id': 3, 'name': u'source-3', 'target': {'id': 1, 'name': u'target-1'}, 'target_source': 1}]},
            {'id': 2, 'name': u'target-source-2', 'target': 2, 'sources': []}
        ]
        self.assertEquals(serializer.data, expected)        

class NestedForeignKeyTests(TestCase):
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
