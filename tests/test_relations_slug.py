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
            {'id': 1, 'name': 'source-1', 'target': 'target-1'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': 'target-1'}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_foreign_key_retrieve_select_related(self):
        queryset = ForeignKeySource.objects.all().select_related('target')
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        with self.assertNumQueries(1):
            serializer.data

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': ['source-1', 'source-2', 'source-3']},
            {'id': 2, 'name': 'target-2', 'sources': []},
        ]
        assert serializer.data == expected

    def test_reverse_foreign_key_retrieve_prefetch_related(self):
        queryset = ForeignKeyTarget.objects.all().prefetch_related('sources')
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        with self.assertNumQueries(2):
            serializer.data

    def test_foreign_key_update(self):
        data = {'id': 1, 'name': 'source-1', 'target': 'target-2'}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 'target-2'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': 'target-1'}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_incorrect_type(self):
        data = {'id': 1, 'name': 'source-1', 'target': 123}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['Object with name=123 does not exist.']}

    def test_reverse_foreign_key_update(self):
        data = {'id': 2, 'name': 'target-2', 'sources': ['source-1', 'source-3']}
        instance = ForeignKeyTarget.objects.get(pk=2)
        serializer = ForeignKeyTargetSerializer(instance, data=data)
        assert serializer.is_valid()
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.all()
        new_serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': ['source-1', 'source-2', 'source-3']},
            {'id': 2, 'name': 'target-2', 'sources': []},
        ]
        assert new_serializer.data == expected

        serializer.save()
        assert serializer.data == data

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': ['source-2']},
            {'id': 2, 'name': 'target-2', 'sources': ['source-1', 'source-3']},
        ]
        assert serializer.data == expected

    def test_foreign_key_create(self):
        data = {'id': 4, 'name': 'source-4', 'target': 'target-2'}
        serializer = ForeignKeySourceSerializer(data=data)
        serializer.is_valid()
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == data
        assert obj.name == 'source-4'

        # Ensure source 4 is added, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 'target-1'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': 'target-1'},
            {'id': 4, 'name': 'source-4', 'target': 'target-2'},
        ]
        assert serializer.data == expected

    def test_reverse_foreign_key_create(self):
        data = {'id': 3, 'name': 'target-3', 'sources': ['source-1', 'source-3']}
        serializer = ForeignKeyTargetSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == data
        assert obj.name == 'target-3'

        # Ensure target 3 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': ['source-2']},
            {'id': 2, 'name': 'target-2', 'sources': []},
            {'id': 3, 'name': 'target-3', 'sources': ['source-1', 'source-3']},
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_invalid_null(self):
        data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['This field may not be null.']}


class SlugNullableForeignKeyTests(TestCase):
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
            {'id': 1, 'name': 'source-1', 'target': 'target-1'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': None},
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_null(self):
        data = {'id': 4, 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == data
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 'target-1'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': None},
            {'id': 4, 'name': 'source-4', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': 4, 'name': 'source-4', 'target': ''}
        expected_data = {'id': 4, 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == expected_data
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 'target-1'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': None},
            {'id': 4, 'name': 'source-4', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_valid_null(self):
        data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': None},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': 1, 'name': 'source-1', 'target': ''}
        expected_data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == expected_data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': None},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': None}
        ]
        assert serializer.data == expected
