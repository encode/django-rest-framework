from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import NullableForeignKeySource, ForeignKeySource, ForeignKeyTarget


class ForeignKeyTargetSerializer(serializers.ModelSerializer):
    sources = serializers.SlugRelatedField(many=True, slug_field='name')

    class Meta:
        model = ForeignKeyTarget


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(slug_field='name')

    class Meta:
        model = ForeignKeySource


class NullableForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(slug_field='name', required=False)

    class Meta:
        model = NullableForeignKeySource


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
        self.assertEqual(serializer.data, expected)

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': ['source-1', 'source-2', 'source-3']},
            {'id': 2, 'name': 'target-2', 'sources': []},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update(self):
        data = {'id': 1, 'name': 'source-1', 'target': 'target-2'}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 'target-2'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': 'target-1'}
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_incorrect_type(self):
        data = {'id': 1, 'name': 'source-1', 'target': 123}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'target': ['Object with name=123 does not exist.']})

    def test_reverse_foreign_key_update(self):
        data = {'id': 2, 'name': 'target-2', 'sources': ['source-1', 'source-3']}
        instance = ForeignKeyTarget.objects.get(pk=2)
        serializer = ForeignKeyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.all()
        new_serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': ['source-1', 'source-2', 'source-3']},
            {'id': 2, 'name': 'target-2', 'sources': []},
        ]
        self.assertEqual(new_serializer.data, expected)

        serializer.save()
        self.assertEqual(serializer.data, data)

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': ['source-2']},
            {'id': 2, 'name': 'target-2', 'sources': ['source-1', 'source-3']},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_create(self):
        data = {'id': 4, 'name': 'source-4', 'target': 'target-2'}
        serializer = ForeignKeySourceSerializer(data=data)
        serializer.is_valid()
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'source-4')

        # Ensure source 4 is added, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'source-1', 'target': 'target-1'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': 'target-1'},
            {'id': 4, 'name': 'source-4', 'target': 'target-2'},
        ]
        self.assertEqual(serializer.data, expected)

    def test_reverse_foreign_key_create(self):
        data = {'id': 3, 'name': 'target-3', 'sources': ['source-1', 'source-3']}
        serializer = ForeignKeyTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(serializer.data, data)
        self.assertEqual(obj.name, 'target-3')

        # Ensure target 3 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True)
        expected = [
            {'id': 1, 'name': 'target-1', 'sources': ['source-2']},
            {'id': 2, 'name': 'target-2', 'sources': []},
            {'id': 3, 'name': 'target-3', 'sources': ['source-1', 'source-3']},
        ]
        self.assertEqual(serializer.data, expected)

    def test_foreign_key_update_with_invalid_null(self):
        data = {'id': 1, 'name': 'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'target': ['This field is required.']})


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
            {'id': 1, 'name': 'source-1', 'target': 'target-1'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
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
            {'id': 1, 'name': 'source-1', 'target': 'target-1'},
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
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
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
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
            {'id': 2, 'name': 'source-2', 'target': 'target-1'},
            {'id': 3, 'name': 'source-3', 'target': None}
        ]
        self.assertEqual(serializer.data, expected)
