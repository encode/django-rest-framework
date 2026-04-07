from django.test import TestCase

from rest_framework import serializers
from tests.models import (
    ForeignKeySource, ForeignKeyTarget, NullableForeignKeySource
)


class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    sources = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ForeignKeySource.objects.all(),
        many=True
    )

    class Meta:
        model = ForeignKeyTarget
        fields = '__all__'


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ForeignKeyTarget.objects.all()
    )

    class Meta:
        model = ForeignKeySource
        fields = '__all__'


class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(
        slug_field='name',
        queryset=ForeignKeyTarget.objects.all(),
        allow_null=True
    )

    class Meta:
        model = NullableForeignKeySource
        fields = '__all__'


# TODO: M2M Tests, FKTests (Non-nullable), One2One
class SlugForeignKeyTests(TestCase):
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
        queryset = ForeignKeySource.objects.all().order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': 'target-1'},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': 'target-1'},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': 'target-1'}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_foreign_key_retrieve_select_related(self):
        queryset = ForeignKeySource.objects.all().order_by('pk').select_related('target')
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        with self.assertNumQueries(1):
            serializer.data

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all().order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target.pk, 'name': 'target-1', 'sources': ['source-1', 'source-2', 'source-3']},
            {'id': self.new_target.pk, 'name': 'target-2', 'sources': []},
        ]
        assert serializer.data == expected

    def test_reverse_foreign_key_retrieve_prefetch_related(self):
        queryset = ForeignKeyTarget.objects.all().order_by('pk').prefetch_related('sources')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        with self.assertNumQueries(2):
            serializer.data

    def test_foreign_key_update(self):
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': 'target-2'}
        instance = ForeignKeySource.objects.get(pk=self.sources[0].pk)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all().order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': 'target-2'},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': 'target-1'},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': 'target-1'}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_incorrect_type(self):
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': 123}
        instance = ForeignKeySource.objects.get(pk=self.sources[0].pk)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['Object with name=123 does not exist.']}

    def test_reverse_foreign_key_update(self):
        data = {'id': self.new_target.pk, 'name': 'target-2', 'sources': ['source-1', 'source-3']}
        instance = ForeignKeyTarget.objects.get(pk=self.new_target.pk)
        serializer = ForeignKeyTargetSerializer(instance, data=data)
        assert serializer.is_valid()
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.all().order_by('pk')
        new_serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target.pk, 'name': 'target-1', 'sources': ['source-1', 'source-2', 'source-3']},
            {'id': self.new_target.pk, 'name': 'target-2', 'sources': []},
        ]
        assert new_serializer.data == expected

        serializer.save()
        assert serializer.data == data

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all().order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target.pk, 'name': 'target-1', 'sources': ['source-2']},
            {'id': self.new_target.pk, 'name': 'target-2', 'sources': ['source-1', 'source-3']},
        ]
        assert serializer.data == expected

    def test_foreign_key_create(self):
        data = {'name': 'source-4', 'target': 'target-2'}
        serializer = ForeignKeySourceSerializer(data=data)
        serializer.is_valid()
        assert serializer.is_valid()
        obj = serializer.save()
        expected_data = {'id': obj.pk, 'name': 'source-4', 'target': 'target-2'}
        assert serializer.data == expected_data
        assert obj.name == 'source-4'

        # Ensure source 4 is added, and everything else is as expected
        queryset = ForeignKeySource.objects.all().order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': 'target-1'},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': 'target-1'},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': 'target-1'},
            {'id': obj.pk, 'name': 'source-4', 'target': 'target-2'},
        ]
        assert serializer.data == expected

    def test_reverse_foreign_key_create(self):
        data = {'name': 'target-3', 'sources': ['source-1', 'source-3']}
        serializer = ForeignKeyTargetSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        expected_data = {'id': obj.pk, 'name': 'target-3', 'sources': ['source-1', 'source-3']}
        assert serializer.data == expected_data
        assert obj.name == 'target-3'

        # Ensure target 3 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all().order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': self.target.pk, 'name': 'target-1', 'sources': ['source-2']},
            {'id': self.new_target.pk, 'name': 'target-2', 'sources': []},
            {'id': obj.pk, 'name': 'target-3', 'sources': ['source-1', 'source-3']},
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_invalid_null(self):
        data = {'id': self.sources[0].pk, 'name': 'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=self.sources[0].pk)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['This field may not be null.']}


class SlugNullableForeignKeyTests(TestCase):
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
        queryset = NullableForeignKeySource.objects.all().order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': 'target-1'},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': 'target-1'},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': None},
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_null(self):
        data = {'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        expected_data = {'id': obj.pk, 'name': 'source-4', 'target': None}
        assert serializer.data == expected_data
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all().order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': 'target-1'},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': 'target-1'},
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
        queryset = NullableForeignKeySource.objects.all().order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': 'target-1'},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': 'target-1'},
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
        queryset = NullableForeignKeySource.objects.all().order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': None},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': 'target-1'},
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
        queryset = NullableForeignKeySource.objects.all().order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': self.sources[0].pk, 'name': 'source-1', 'target': None},
            {'id': self.sources[1].pk, 'name': 'source-2', 'target': 'target-1'},
            {'id': self.sources[2].pk, 'name': 'source-3', 'target': None}
        ]
        assert serializer.data == expected
