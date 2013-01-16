from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import NullableForeignKeySource, ForeignKeyTarget


class NullableSlugSourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(slug_field='name', null=True)

    class Meta:
        model = NullableForeignKeySource


# TODO: M2M Tests, FKTests (Non-nulable), One2One

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
        serializer = NullableSlugSourceSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': 'target-1'},
            {'id': 2, 'name': u'source-2', 'target': 'target-1'},
            {'id': 3, 'name': u'source-3', 'target': None},
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_create_with_valid_null(self):
        data = {'id': 4, 'name': u'source-4', 'target': None}
        serializer = NullableSlugSourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableSlugSourceSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': 'target-1'},
            {'id': 2, 'name': u'source-2', 'target': 'target-1'},
            {'id': 3, 'name': u'source-3', 'target': None},
            {'id': 4, 'name': u'source-4', 'target': None}
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': 4, 'name': u'source-4', 'target': ''}
        expected_data = {'id': 4, 'name': u'source-4', 'target': None}
        serializer = NullableSlugSourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, expected_data)
        self.assertEqual(obj.name, u'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableSlugSourceSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': 'target-1'},
            {'id': 2, 'name': u'source-2', 'target': 'target-1'},
            {'id': 3, 'name': u'source-3', 'target': None},
            {'id': 4, 'name': u'source-4', 'target': None}
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_update_with_valid_null(self):
        data = {'id': 1, 'name': u'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableSlugSourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableSlugSourceSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': None},
            {'id': 2, 'name': u'source-2', 'target': 'target-1'},
            {'id': 3, 'name': u'source-3', 'target': None}
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'id': 1, 'name': u'source-1', 'target': ''}
        expected_data = {'id': 1, 'name': u'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableSlugSourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, expected_data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableSlugSourceSerializer(queryset)
        expected = [
            {'id': 1, 'name': u'source-1', 'target': None},
            {'id': 2, 'name': u'source-2', 'target': 'target-1'},
            {'id': 3, 'name': u'source-3', 'target': None}
        ]
        self.assertEquals(serializer.data, expected)
