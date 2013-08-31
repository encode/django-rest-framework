from __future__ import unicode_literals
from django.db import models
from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import (
    BlogPost, ManyToManyTarget, ManyToManySource, ForeignKeyTarget, ForeignKeySource,
    NullableForeignKeySource, OneToOneTarget, NullableOneToOneSource,
)
from rest_framework.compat import six


# ManyToMany
class ManyToManyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManyTarget
        fields = ('id', 'name', 'sources')


class ManyToManySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManySource
        fields = ('id', 'name', 'targets')


# ForeignKey
class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeyTarget
        fields = ('id', 'name', 'sources')


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = ('id', 'name', 'target')


# Nullable ForeignKey
class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NullableForeignKeySource
        fields = ('id', 'name', 'target')


# Nullable OneToOne
class NullableOneToOneTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneToOneTarget
        fields = ('id', 'name', 'nullable_source')


# TODO: Add test that .data cannot be accessed prior to .is_valid

class PKManyToManyTests(TestCase):
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
        serializer = ManyToManySourceSerializer(queryset, many=True)
        expected = [
                {'id': 1, 'name': 'source-1', 'targets': [1]},
                {'id': 2, 'name': 'source-2', 'targets': [1, 2]},
                {'id': 3, 'name': 'source-3', 'targets': [1, 2, 3]}
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_many_to_many_retrieve(self):
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': 'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': 'target-3', 'sources': [3]}
        ]
        self.assertEqual(serializer.data, expected)

    def test_many_to_many_update(self):
        data = {'id': 1, 'name': 'source-1', 'targets': [1, 2, 3]}
        instance = ManyToManySource.objects.get(pk=1)
        serializer = ManyToManySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True)
        expected = [
                {'id': 1, 'name': 'source-1', 'targets': [1, 2, 3]},
                {'id': 2, 'name': 'source-2', 'targets': [1, 2]},
                {'id': 3, 'name': 'source-3', 'targets': [1, 2, 3]}
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_many_to_many_update(self):
        data = {'id': 1, 'name': 'target-1', 'sources': [1]}
        instance = ManyToManyTarget.objects.get(pk=1)
        serializer = ManyToManyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure target 1 is updated, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1]},
            {'id': 2, 'name': 'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': 'target-3', 'sources': [3]}
        ]
        self.assertEqual(serializer.data, expected)

    def test_many_to_many_create(self):
        data = {'id': 4, 'name': 'source-4', 'targets': [1, 3]}
        serializer = ManyToManySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is added, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True)
        self.assertFalse(serializer.fields['targets'].read_only)
        expected = [
            {'id': 1, 'name': 'source-1', 'targets': [1]},
            {'id': 2, 'name': 'source-2', 'targets': [1, 2]},
            {'id': 3, 'name': 'source-3', 'targets': [1, 2, 3]},
            {'id': 4, 'name': 'source-4', 'targets': [1, 3]},
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_many_to_many_create(self):
        data = {'id': 4, 'name': 'target-4', 'sources': [1, 3]}
        serializer = ManyToManyTargetSerializer(data=data)
        self.assertFalse(serializer.fields['sources'].read_only)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'target-4')

        # Ensure target 4 is added, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': 'target-2', 'sources': [2, 3]},
            {'id': 3, 'name': 'target-3', 'sources': [3]},
            {'id': 4, 'name': 'target-4', 'sources': [1, 3]}
        ]
        self.assertEqual(serializer.data, expected)


class PKForeignKeyTests(TestCase):
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
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': 1}
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': 'target-2', 'sources': []},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update(self):
        data = {'id': 1, 'name': 'source-1', 'target': 2}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 2},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': 1}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_incorrect_type(self):
        data = {'id': 1, 'name': 'source-1', 'target': 'foo'}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'target': ['Incorrect type.  Expected pk value, received %s.' % six.text_type.__name__]})

    def test_reverse_foreign_key_update(self):
        data = {'id': 2, 'name': 'target-2', 'sources': [1, 3]}
        instance = ForeignKeyTarget.objects.get(pk=2)
        serializer = ForeignKeyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.all()
        new_serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [1, 2, 3]},
            {'id': 2, 'name': 'target-2', 'sources': []},
        ]
        self.assertEqual(new_serializer.data, expected)

        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [2]},
            {'id': 2, 'name': 'target-2', 'sources': [1, 3]},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_create(self):
        data = {'id': 4, 'name': 'source-4', 'target': 2}
        serializer = ForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is added, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': 1},
            {'id': 4, 'name': 'source-4', 'target': 2},
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_foreign_key_create(self):
        data = {'id': 3, 'name': 'target-3', 'sources': [1, 3]}
        serializer = ForeignKeyTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'target-3')

        # Ensure target 3 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': [2]},
            {'id': 2, 'name': 'target-2', 'sources': []},
            {'id': 3, 'name': 'target-3', 'sources': [1, 3]},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_with_invalid_null(self):
        data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'target': ['This field is required.']})

    def test_foreign_key_with_empty(self):
        """
        Regression test for #1072

        https://github.com/tomchristie/django-rest-framework/issues/1072
        """
        serializer = NullableForeignKeySourceSerializer()
        self.assertEqual(serializer.data['target'], None)


class PKNullableForeignKeyTests(TestCase):
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
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_create_with_valid_null(self):
        data = {'id': 4, 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None},
            {'id': 4, 'name': 'source-4', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': 4, 'name': 'source-4', 'target': ''}
        expected_data = {'id': 4, 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, expected_data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 1},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None},
            {'id': 4, 'name': 'source-4', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_with_valid_null(self):
        data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': None},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': 1, 'name': 'source-1', 'target': ''}
        expected_data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, expected_data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': None},
            {'id': 2, 'name': 'source-2', 'target': 1},
            {'id': 3, 'name': 'source-3', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)

    # reverse foreign keys MUST be read_only
    # In the general case they do not provide .remove() or .clear()
    # and cannot be arbitrarily set.

    # def test_reverse_foreign_key_update(self):
    #     data = {'id': 1, 'name': 'target-1', 'sources': [1]}
    #     instance = ForeignKeyTarget.objects.get(pk=1)
    #     serializer = ForeignKeyTargetSerializer(instance, data=data)
    #     self.assertTrue(serializer.is_valid())
    #     self.assertEqual(serializer.data, data)
    #     serializer.save()

    #     # Ensure target 1 is updated, and everything else is as expected
    #     queryset = ForeignKeyTarget.objects.all()
    #     serializer = ForeignKeyTargetSerializer(queryset, many=True)
    #     expected = [
    #         {'id': 1, 'name': 'target-1', 'sources': [1]},
    #         {'id': 2, 'name': 'target-2', 'sources': []},
    #     ]
    #     self.assertEqual(serializer.data, expected)


class PKNullableOneToOneTests(TestCase):
    def setUp(self):
        target = OneToOneTarget(name='target-1')
        target.save()
        new_target = OneToOneTarget(name='target-2')
        new_target.save()
        source = NullableOneToOneSource(name='source-1', target=new_target)
        source.save()

    def test_reverse_foreign_key_retrieve_with_null(self):
        queryset = OneToOneTarget.objects.all()
        serializer = NullableOneToOneTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'nullable_source': None},
            {'id': 2, 'name': 'target-2', 'nullable_source': 1},
        ]
        self.assertEqual(serializer.data, expected)


# The below models and tests ensure that serializer fields corresponding
# to a ManyToManyField field with a user-specified ``through`` model are
# set to read only


class ManyToManyThroughTarget(models.Model):
    name = models.CharField(max_length=100)


class ManyToManyThrough(models.Model):
    source = models.ForeignKey('ManyToManyThroughSource')
    target = models.ForeignKey(ManyToManyThroughTarget)


class ManyToManyThroughSource(models.Model):
    name = models.CharField(max_length=100)
    targets = models.ManyToManyField(ManyToManyThroughTarget,
                                     related_name='sources',
                                     through='ManyToManyThrough')


class ManyToManyThroughTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManyThroughTarget
        fields = ('id', 'name', 'sources')


class ManyToManyThroughSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManyThroughSource
        fields = ('id', 'name', 'targets')


class PKManyToManyThroughTests(TestCase):
    def setUp(self):
        self.source = ManyToManyThroughSource.objects.create(
            name='through-source-1')
        self.target = ManyToManyThroughTarget.objects.create(
            name='through-target-1')

    def test_many_to_many_create(self):
        data = {'id': 2, 'name': 'source-2', 'targets': [self.target.pk]}
        serializer = ManyToManyThroughSourceSerializer(data=data)
        self.assertTrue(serializer.fields['targets'].read_only)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(obj.name, 'source-2')
        self.assertEqual(obj.targets.count(), 0)

    def test_many_to_many_reverse_create(self):
        data = {'id': 2, 'name': 'target-2', 'sources': [self.source.pk]}
        serializer = ManyToManyThroughTargetSerializer(data=data)
        self.assertTrue(serializer.fields['sources'].read_only)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        obj = serializer.save()
        self.assertEqual(obj.name, 'target-2')
        self.assertEqual(obj.sources.count(), 0)


# Regression tests for #694 (`source` attribute on related fields)


class PrimaryKeyRelatedFieldSourceTests(TestCase):
    def test_related_manager_source(self):
        """
        Relational fields should be able to use manager-returning methods as their source.
        """
        BlogPost.objects.create(title='blah')
        field = serializers.PrimaryKeyRelatedField(many=True, source='get_blogposts_manager')

        class ClassWithManagerMethod(object):
            def get_blogposts_manager(self):
                return BlogPost.objects

        obj = ClassWithManagerMethod()
        value = field.field_to_native(obj, 'field_name')
        self.assertEqual(value, [1])

    def test_related_queryset_source(self):
        """
        Relational fields should be able to use queryset-returning methods as their source.
        """
        BlogPost.objects.create(title='blah')
        field = serializers.PrimaryKeyRelatedField(many=True, source='get_blogposts_queryset')

        class ClassWithQuerysetMethod(object):
            def get_blogposts_queryset(self):
                return BlogPost.objects.all()

        obj = ClassWithQuerysetMethod()
        value = field.field_to_native(obj, 'field_name')
        self.assertEqual(value, [1])

    def test_dotted_source(self):
        """
        Source argument should support dotted.source notation.
        """
        BlogPost.objects.create(title='blah')
        field = serializers.PrimaryKeyRelatedField(many=True, source='a.b.c')

        class ClassWithQuerysetMethod(object):
            a = {
                'b': {
                    'c': BlogPost.objects.all()
                }
            }

        obj = ClassWithQuerysetMethod()
        value = field.field_to_native(obj, 'field_name')
        self.assertEqual(value, [1])
