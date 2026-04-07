import pytest
from django.test import TestCase

from rest_framework import serializers
from tests.models import (
    ForeignKeySource, ForeignKeySourceWithLimitedChoices,
    ForeignKeySourceWithQLimitedChoices, ForeignKeyTarget, ManyToManySource,
    ManyToManyTarget, NullableForeignKeySource, NullableOneToOneSource,
    NullableUUIDForeignKeySource, OneToOnePKSource, OneToOneTarget,
    UUIDForeignKeyTarget
)


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


class ForeignKeyTargetCallableSourceSerializer(serializers.ModelSerializer):
    first_source = serializers.PrimaryKeyRelatedField(
        source='get_first_source',
        read_only=True,
    )

    class Meta:
        model = ForeignKeyTarget
        fields = ('id', 'name', 'first_source')


class ForeignKeyTargetPropertySourceSerializer(serializers.ModelSerializer):
    first_source = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ForeignKeyTarget
        fields = ('id', 'name', 'first_source')


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = ('id', 'name', 'target')


class ForeignKeySourceWithLimitedChoicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySourceWithLimitedChoices
        fields = ("id", "target")


# Nullable ForeignKey
class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NullableForeignKeySource
        fields = ('id', 'name', 'target')


# Nullable UUIDForeignKey
class NullableUUIDForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.PrimaryKeyRelatedField(
        pk_field=serializers.UUIDField(),
        queryset=UUIDForeignKeyTarget.objects.all(),
        allow_null=True)

    class Meta:
        model = NullableUUIDForeignKeySource
        fields = ('id', 'name', 'target')


# Nullable OneToOne
class NullableOneToOneTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneToOneTarget
        fields = ('id', 'name', 'nullable_source')


class OneToOnePKSourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = OneToOnePKSource
        fields = '__all__'


class PKManyToManyTests(TestCase):
    def setUp(self):
        self.targets = []
        self.sources = []
        for idx in range(1, 4):
            target = ManyToManyTarget(name='target-%d' % idx)
            target.save()
            self.targets.append(target)
            source = ManyToManySource(name='source-%d' % idx)
            source.save()
            self.sources.append(source)
            for target in ManyToManyTarget.objects.all():
                source.targets.add(target)

    def test_many_to_many_retrieve(self):
        queryset = ManyToManySource.objects.order_by('pk')
        serializer = ManyToManySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'targets': [self.targets[0].pk]},
            {'id': self.sources[1].pk, 'name': 'source-2', 'targets': [self.targets[0].pk, self.targets[1].pk]},
            {'id': self.sources[2].pk, 'name': 'source-3', 'targets': [self.targets[0].pk, self.targets[1].pk, self.targets[2].pk]}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_many_to_many_retrieve_prefetch_related(self):
        queryset = ManyToManySource.objects.order_by('pk').prefetch_related('targets')
        serializer = ManyToManySourceSerializer(queryset, many=True)
        with self.assertNumQueries(2):
            serializer.data

    def test_reverse_many_to_many_retrieve(self):
        queryset = ManyToManyTarget.objects.order_by('pk')
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.targets[0].pk, 'name': 'target-1', 'sources': [self.sources[0].pk, self.sources[1].pk, self.sources[2].pk]},
            {'id': self.targets[1].pk, 'name': 'target-2', 'sources': [self.sources[1].pk, self.sources[2].pk]},
            {'id': self.targets[2].pk, 'name': 'target-3', 'sources': [self.sources[2].pk]}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_many_to_many_update(self):
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'targets': [self.targets[0].pk, self.targets[1].pk, self.targets[2].pk]}
        instance = ManyToManySource.objects.get(pk=self.sources[0].pk)
        serializer = ManyToManySourceSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ManyToManySource.objects.order_by('pk')
        serializer = ManyToManySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'targets': [self.targets[0].pk, self.targets[1].pk, self.targets[2].pk]},
            {'id': self.sources[1].pk, 'name': 'source-2', 'targets': [self.targets[0].pk, self.targets[1].pk]},
            {'id': self.sources[2].pk, 'name': 'source-3', 'targets': [self.targets[0].pk, self.targets[1].pk, self.targets[2].pk]}
        ]
        assert serializer.data == expected

    def test_reverse_many_to_many_update(self):
        data = {'id': self.targets[0].pk, 'name': 'target-1', 'sources': [self.sources[0].pk]}
        instance = ManyToManyTarget.objects.get(pk=self.targets[0].pk)
        serializer = ManyToManyTargetSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure target 1 is updated, and everything else is as expected
        queryset = ManyToManyTarget.objects.order_by('pk')
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.targets[0].pk, 'name': 'target-1', 'sources': [self.sources[0].pk]},
            {'id': self.targets[1].pk, 'name': 'target-2', 'sources': [self.sources[1].pk, self.sources[2].pk]},
            {'id': self.targets[2].pk, 'name': 'target-3', 'sources': [self.sources[2].pk]}
        ]
        assert serializer.data == expected

    def test_many_to_many_create(self):
        data = {'name': 'source-4', 'targets': [self.targets[0].pk, self.targets[2].pk]}
        serializer = ManyToManySourceSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == {'id': obj.pk, 'name': 'source-4', 'targets': [self.targets[0].pk, self.targets[2].pk]}
        assert obj.name == 'source-4'

        # Ensure source 4 is added, and everything else is as expected
        queryset = ManyToManySource.objects.order_by('pk')
        serializer = ManyToManySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'targets': [self.targets[0].pk]},
            {'id': self.sources[1].pk, 'name': 'source-2', 'targets': [self.targets[0].pk, self.targets[1].pk]},
            {'id': self.sources[2].pk, 'name': 'source-3', 'targets': [self.targets[0].pk, self.targets[1].pk, self.targets[2].pk]},
            {'id': obj.pk, 'name': 'source-4', 'targets': [self.targets[0].pk, self.targets[2].pk]},
        ]
        assert serializer.data == expected

    def test_many_to_many_unsaved(self):
        source = ManyToManySource(name='source-unsaved')

        serializer = ManyToManySourceSerializer(source)

        expected = {'id': None, 'name': 'source-unsaved', 'targets': []}
        # no query if source hasn't been created yet
        with self.assertNumQueries(0):
            assert serializer.data == expected

    def test_reverse_many_to_many_create(self):
        data = {'name': 'target-4', 'sources': [self.sources[0].pk, self.sources[2].pk]}
        serializer = ManyToManyTargetSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == {'id': obj.pk, 'name': 'target-4', 'sources': [self.sources[0].pk, self.sources[2].pk]}
        assert obj.name == 'target-4'

        # Ensure target 4 is added, and everything else is as expected
        queryset = ManyToManyTarget.objects.order_by('pk')
        serializer = ManyToManyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.targets[0].pk, 'name': 'target-1', 'sources': [self.sources[0].pk, self.sources[1].pk, self.sources[2].pk]},
            {'id': self.targets[1].pk, 'name': 'target-2', 'sources': [self.sources[1].pk, self.sources[2].pk]},
            {'id': self.targets[2].pk, 'name': 'target-3', 'sources': [self.sources[2].pk]},
            {'id': obj.pk, 'name': 'target-4', 'sources': [self.sources[0].pk, self.sources[2].pk]}
        ]
        assert serializer.data == expected

    def test_data_cannot_be_accessed_prior_to_is_valid(self):
        """Test that .data cannot be accessed prior to .is_valid for primary key serializers."""
        serializer = ManyToManySourceSerializer(
            data={'name': 'test-source', 'targets': [self.targets[0].pk]}
        )
        with pytest.raises(AssertionError):
            serializer.data


class PKForeignKeyTests(TestCase):
    def setUp(self):
        self.target = ForeignKeyTarget(name='target-1')
        self.target.save()
        self.new_target = ForeignKeyTarget(name='target-2')
        self.new_target.save()
        self.sources = []
        for idx in range(1, 4):
            source = ForeignKeySource(name='source-%d' % idx, target=self.target)
            source.save()
            self.sources.append(source)

    def test_foreign_key_retrieve(self):
        queryset = ForeignKeySource.objects.order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': self.target.pk},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': self.target.pk},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': self.target.pk}
        ]
        with self.assertNumQueries(1):
            assert serializer.data == expected

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target.pk, 'name': 'target-1', 'sources': [self.sources[0].pk, self.sources[1].pk, self.sources[2].pk]},
            {'id': self.new_target.pk, 'name': 'target-2', 'sources': []},
        ]
        with self.assertNumQueries(3):
            assert serializer.data == expected

    def test_reverse_foreign_key_retrieve_prefetch_related(self):
        queryset = ForeignKeyTarget.objects.order_by('pk').prefetch_related('sources')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        with self.assertNumQueries(2):
            serializer.data

    def test_foreign_key_update(self):
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': self.new_target.pk}
        instance = ForeignKeySource.objects.get(pk=self.sources[0].pk)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': self.new_target.pk},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': self.target.pk},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': self.target.pk}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_incorrect_type(self):
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': 'foo'}
        instance = ForeignKeySource.objects.get(pk=self.sources[0].pk)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['Incorrect type. Expected pk value, received str.']}

    def test_reverse_foreign_key_update(self):
        data = {'id': self.new_target.pk, 'name': 'target-2', 'sources': [self.sources[0].pk, self.sources[2].pk]}
        instance = ForeignKeyTarget.objects.get(pk=self.new_target.pk)
        serializer = ForeignKeyTargetSerializer(instance, data=data)
        assert serializer.is_valid()
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.order_by('pk')
        new_serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target.pk, 'name': 'target-1', 'sources': [self.sources[0].pk, self.sources[1].pk, self.sources[2].pk]},
            {'id': self.new_target.pk, 'name': 'target-2', 'sources': []},
        ]
        assert new_serializer.data == expected

        serializer.save()
        assert serializer.data == data

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target.pk, 'name': 'target-1', 'sources': [self.sources[1].pk]},
            {'id': self.new_target.pk, 'name': 'target-2', 'sources': [self.sources[0].pk, self.sources[2].pk]},
        ]
        assert serializer.data == expected

    def test_foreign_key_create(self):
        data = {'name': 'source-4', 'target': self.new_target.pk}
        serializer = ForeignKeySourceSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == {'id': obj.pk, 'name': 'source-4', 'target': self.new_target.pk}
        assert obj.name == 'source-4'

        # Ensure source 4 is added, and everything else is as expected
        queryset = ForeignKeySource.objects.order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': self.target.pk},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': self.target.pk},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': self.target.pk},
            {'id': obj.pk, 'name': 'source-4', 'target': self.new_target.pk},
        ]
        assert serializer.data == expected

    def test_reverse_foreign_key_create(self):
        data = {'name': 'target-3', 'sources': [self.sources[0].pk, self.sources[2].pk]}
        serializer = ForeignKeyTargetSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == {'id': obj.pk, 'name': 'target-3', 'sources': [self.sources[0].pk, self.sources[2].pk]}
        assert obj.name == 'target-3'

        # Ensure target 3 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target.pk, 'name': 'target-1', 'sources': [self.sources[1].pk]},
            {'id': self.new_target.pk, 'name': 'target-2', 'sources': []},
            {'id': obj.pk, 'name': 'target-3', 'sources': [self.sources[0].pk, self.sources[2].pk]},
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_invalid_null(self):
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=self.sources[0].pk)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['This field may not be null.']}

    def test_foreign_key_with_unsaved(self):
        source = ForeignKeySource(name='source-unsaved')
        expected = {'id': None, 'name': 'source-unsaved', 'target': None}

        serializer = ForeignKeySourceSerializer(source)

        # no query if source hasn't been created yet
        with self.assertNumQueries(0):
            assert serializer.data == expected

    def test_foreign_key_with_empty(self):
        """
        Regression test for #1072

        https://github.com/encode/django-rest-framework/issues/1072
        """
        serializer = NullableForeignKeySourceSerializer()
        assert serializer.data['target'] is None

    def test_foreign_key_not_required(self):
        """
        Let's say we wanted to fill the non-nullable model field inside
        Model.save(), we would make it empty and not required.
        """
        class ModelSerializer(ForeignKeySourceSerializer):
            class Meta(ForeignKeySourceSerializer.Meta):
                extra_kwargs = {'target': {'required': False}}
        serializer = ModelSerializer(data={'name': 'test'})
        serializer.is_valid(raise_exception=True)
        assert 'target' not in serializer.validated_data

    def test_queryset_size_without_limited_choices(self):
        limited_target = ForeignKeyTarget(name="limited-target")
        limited_target.save()
        queryset = ForeignKeySourceSerializer().fields["target"].get_queryset()
        assert len(queryset) == 3

    def test_queryset_size_with_limited_choices(self):
        limited_target = ForeignKeyTarget(name="limited-target")
        limited_target.save()
        queryset = ForeignKeySourceWithLimitedChoicesSerializer().fields["target"].get_queryset()
        assert len(queryset) == 1

    def test_queryset_size_with_Q_limited_choices(self):
        limited_target = ForeignKeyTarget(name="limited-target")
        limited_target.save()

        class QLimitedChoicesSerializer(serializers.ModelSerializer):
            class Meta:
                model = ForeignKeySourceWithQLimitedChoices
                fields = ("id", "target")

        queryset = QLimitedChoicesSerializer().fields["target"].get_queryset()
        assert len(queryset) == 1


class PKRelationTests(TestCase):

    def setUp(self):
        self.target = ForeignKeyTarget.objects.create(name='target-1')
        self.source1 = ForeignKeySource.objects.create(name='source-1', target=self.target)
        self.source2 = ForeignKeySource.objects.create(name='source-2', target=self.target)

    def test_relation_field_callable_source(self):
        serializer = ForeignKeyTargetCallableSourceSerializer(self.target)
        expected = {
            'id': self.target.pk,
            'name': 'target-1',
            'first_source': self.source1.pk,
        }
        with self.assertNumQueries(1):
            self.assertEqual(serializer.data, expected)

    def test_relation_field_property_source(self):
        serializer = ForeignKeyTargetPropertySourceSerializer(self.target)
        expected = {
            'id': self.target.pk,
            'name': 'target-1',
            'first_source': self.source1.pk,
        }
        with self.assertNumQueries(1):
            self.assertEqual(serializer.data, expected)


class PKNullableForeignKeyTests(TestCase):
    def setUp(self):
        self.target = ForeignKeyTarget(name='target-1')
        self.target.save()
        self.sources = []
        for idx in range(1, 4):
            target = self.target
            if idx == 3:
                target = None
            source = NullableForeignKeySource(name='source-%d' % idx, target=target)
            source.save()
            self.sources.append(source)

    def test_foreign_key_retrieve_with_null(self):
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': self.target.pk},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': self.target.pk},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': None},
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_null(self):
        data = {'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == {'id': obj.pk, 'name': 'source-4', 'target': None}
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': self.target.pk},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': self.target.pk},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': None},
            {'id': obj.pk, 'name': 'source-4', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'name': 'source-4', 'target': ''}
        serializer = NullableForeignKeySourceSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        expected_data = {'id': obj.pk, 'name': 'source-4', 'target': None}
        assert serializer.data == expected_data
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': self.target.pk},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': self.target.pk},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': None},
            {'id': obj.pk, 'name': 'source-4', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_valid_null(self):
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=self.sources[0].pk)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': None},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': self.target.pk},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': ''}
        expected_data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=self.sources[0].pk)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == expected_data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': None},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': self.target.pk},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': None}
        ]
        assert serializer.data == expected

    def test_null_uuid_foreign_key_serializes_as_none(self):
        source = NullableUUIDForeignKeySource(name='Source')
        serializer = NullableUUIDForeignKeySourceSerializer(source)
        data = serializer.data
        assert data["target"] is None

    def test_nullable_uuid_foreign_key_is_valid_when_none(self):
        data = {"name": "Source", "target": None}
        serializer = NullableUUIDForeignKeySourceSerializer(data=data)
        assert serializer.is_valid(), serializer.errors


class PKNullableOneToOneTests(TestCase):
    def setUp(self):
        self.target1 = OneToOneTarget(name='target-1')
        self.target1.save()
        self.target2 = OneToOneTarget(name='target-2')
        self.target2.save()
        self.source = NullableOneToOneSource(name='source-1', target=self.target2)
        self.source.save()

    def test_reverse_foreign_key_retrieve_with_null(self):
        queryset = OneToOneTarget.objects.order_by('pk')
        serializer = NullableOneToOneTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target1.pk, 'name': 'target-1', 'nullable_source': None},
            {'id': self.target2.pk, 'name': 'target-2', 'nullable_source': self.source.pk},
        ]
        assert serializer.data == expected


class OneToOnePrimaryKeyTests(TestCase):

    def setUp(self):
        # Given: Some target models already exist
        self.target = target = OneToOneTarget(name='target-1')
        target.save()
        self.alt_target = alt_target = OneToOneTarget(name='target-2')
        alt_target.save()

    def test_one_to_one_when_primary_key(self):
        # When: Creating a Source pointing at the id of the second Target
        target_pk = self.alt_target.id
        source = OneToOnePKSourceSerializer(data={'name': 'source-2', 'target': target_pk})
        # Then: The source is valid with the serializer
        if not source.is_valid():
            self.fail(f"Expected OneToOnePKTargetSerializer to be valid but had errors: {source.errors}")
        # Then: Saving the serializer creates a new object
        new_source = source.save()
        # Then: The new object has the same pk as the target object
        self.assertEqual(new_source.pk, target_pk)

    def test_one_to_one_when_primary_key_no_duplicates(self):
        # When: Creating a Source pointing at the id of the second Target
        target_pk = self.target.id
        data = {'name': 'source-1', 'target': target_pk}
        source = OneToOnePKSourceSerializer(data=data)
        # Then: The source is valid with the serializer
        self.assertTrue(source.is_valid())
        # Then: Saving the serializer creates a new object
        new_source = source.save()
        # Then: The new object has the same pk as the target object
        self.assertEqual(new_source.pk, target_pk)
        # When: Trying to create a second object
        second_source = OneToOnePKSourceSerializer(data=data)
        self.assertFalse(second_source.is_valid())
        expected = {'target': ['one to one pk source with this target already exists.']}
        self.assertDictEqual(second_source.errors, expected)

    def test_one_to_one_when_primary_key_does_not_exist(self):
        # Given: a target PK that does not exist
        target_pk = self.target.pk + self.alt_target.pk
        source = OneToOnePKSourceSerializer(data={'name': 'source-2', 'target': target_pk})
        # Then: The source is not valid with the serializer
        self.assertFalse(source.is_valid())
        self.assertIn("Invalid pk", source.errors['target'][0])
        self.assertIn("object does not exist", source.errors['target'][0])
