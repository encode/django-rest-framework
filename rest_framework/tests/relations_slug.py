from django.test import TestCase
from rest_framework import serializers
from rest_framework.compat import patterns, url
from rest_framework.tests.models import NullableForeignKeySource, ForeignKeyTarget

def dummy_view(request, pk):
    pass


# Nullable ForeignKey
class SluggedNullableForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(slug_field='name')
    class Meta:
        model = NullableForeignKeySource

class NullOKSluggedNullableForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(slug_field='name', null=True)
    class Meta:
        model = NullableForeignKeySource

class DefaultSluggedNullableForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(slug_field='name', default='N/A')
    class Meta:
        model = NullableForeignKeySource

class NotRequiredSluggedNullableForeignKeySourceSerializer(serializers.ModelSerializer):
    target = serializers.SlugRelatedField(slug_field='name', required=False)
    class Meta:
        model = NullableForeignKeySource


class SluggedNullableForeignKeyTests(TestCase):

    def setUp(self):
        target = ForeignKeyTarget(name='target-1')
        target.save()
        for idx in range(1, 4):
            if idx == 3:
                target = None
            source = NullableForeignKeySource(name='source-%d' % idx, target=target)
            source.save()

    def test_slug_foreign_key_retrieve_with_null(self):
        queryset = NullableForeignKeySource.objects.all()

        default_expected = [
            {'name': u'source-1', 'target': 'target-1'},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': 'N/A'},
        ]
        expected = [
            {'name': u'source-1', 'target': 'target-1'},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': None},
        ]

        serializer = DefaultSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, default_expected)

        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)

        serializer = NullOKSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)

        serializer = SluggedNullableForeignKeySourceSerializer(queryset)
        #Throws 
        self.assertEquals(serializer.data, expected)

    def test_slug_foreign_key_create_with_valid_null(self):
        data = {'name': u'source-4', 'target': None}
        default_data = {'name': u'source-4', 'target': 'N/A'}

        serializer = SluggedNullableForeignKeySourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'target': [u'Value may not be null']})


        #If attribute not required, data should match
        serializer = NullOKSluggedNullableForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        #BUG: Throws AttributeError: "NoneType object has no attribute 'name'"
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'source-4')

        #If default = 'N/A' then target should pass validation, and be the default ('N/A')
        serializer = DefaultSluggedNullableForeignKeySourceSerializer(data=data)
        #BUG: test case fails
        self.assertTrue(serializer.is_valid())
        #BUG: serializer.errors = {'target': [u'Value may not be null']}
        #BUG: Serializer does not use default value to save object
        obj = serializer.save()
        #BUG: Throws AttributeError - NoneType object has no attribute 'name'
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'source-4')

        #If null = True then target should be None
        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(data=data)
        #BUG: test case fails
        self.assertTrue(serializer.is_valid())
        #BUG: serializer.errors = {'target': [u'Value may not be null']}
        #BUG: serializer does not save object (But it can because its not required)
        obj = serializer.save()
        #BUG: Throws AttributeError - NoneType object has no attribute 'name'
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        default_expected = [
            {'name': u'source-1', 'target': 'target-1'},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': 'N/A'},
            {'name': u'source-4', 'target': 'N/A'}
        ]
        expected = [
            {'name': u'source-1', 'target': 'target-1'},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': None},
            {'name': u'source-4', 'target': None}
        ]
        serializer = NullOKSluggedNullableForeignKeySourceSerializer(data=data)
        self.assertEquals(serializer.data, expected)
        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(data=data)
        self.assertEquals(serializer.data, expected)
        serializer = DefaultSluggedNullableForeignKeySourceSerializer(data=data)
        self.assertEquals(serializer.data, default_expected)

    def test_slug_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'name': u'source-4', 'target': ''}
        expected_data = {'name': u'source-4', 'target': None}

        serializer = SluggedNullableForeignKeySourceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'target': [u'Value may not be null']})

        serializer = NullOKSluggedNullableForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        #BUG: Throws AttributeError: 'NoneType' object has no attribute 'name'
        self.assertEquals(serializer.data, expected_data)
        self.assertEqual(obj.name, u'source-4')

        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(data=data)
        #BUG: is_valid() is False
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        #BUG: Throws AttributeError: 'NoneType' object has no attribute 'name'
        self.assertEquals(serializer.data, expected_data)
        self.assertEqual(obj.name, u'source-4')

        serializer = DefaultSluggedNullableForeignKeySourceSerializer(data=data)
        #BUG: is_valid() is False
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        #BUG: Throws AttributeError: 'NoneType' object has no attribute 'name'
        self.assertEquals(serializer.data, expected_data)
        self.assertEqual(obj.name, u'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        default_expected = [
            {'name': u'source-1', 'target': 'target-1'},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': 'N/A'},
            {'name': u'source-4', 'target': 'N/A'}
        ]
        expected = [
            {'name': u'source-1', 'target': 'target-1'},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': None},
            {'name': u'source-4', 'target': None}
        ]
        #BUG: All serializers fail here
        serializer = DefaultSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, default_expected)
        serializer = NullOKSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)
        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)

    def test_slug_foreign_key_update_with_valid_null(self):
        data = {'name': u'source-1', 'target': None}
        default_data = {'name': u'source-1', 'target': 'N/A'}
        instance = NullableForeignKeySource.objects.get(pk=1)

        serializer = SluggedNullableForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'target': [u'Value may not be null']})

        serializer = DefaultSluggedNullableForeignKeySourceSerializer(instance, data=data)
        #BUG: is_valid() is False
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, default_data)
        serializer.save()

        serializer = NullOKSluggedNullableForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        #BUG: Throws AttributeError: 'NoneType' object has no attribute 'name'
        self.assertEquals(serializer.data, data)
        serializer.save()


        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(instance, data=data)
        #BUG: is_valid() is False
        self.assertTrue(serializer.is_valid())
        #BUG: Throws AttributeError: 'NoneType' object has no attribute 'name'
        self.assertEquals(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        expected = [
            {'name': u'source-1', 'target': None},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': None},
        ]
        serializer = NullOKSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)

        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)

        expected = [
            {'name': u'source-1', 'target': 'N/A'},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': 'N/A'},
        ]
        serializer = NullOKSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)

    def test_slug_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'name': u'source-1', 'target': ''}
        default_data = {'name': u'source-1', 'target': 'N/A'}
        expected_data = {'name': u'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)

        serializer = SluggedNullableForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'target': [u'Value may not be null']})

        serializer = DefaultSluggedNullableForeignKeySourceSerializer(instance, data=data)
        #BUG: is_valid() is False
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, default_data)
        serializer.save()

        serializer = NullOKSluggedNullableForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        #BUG: Throws AttributeError: 'NoneType' object has no attribute 'name'
        self.assertEquals(serializer.data, data)
        serializer.save()

        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(instance, data=data)
        #BUG: is_valid() is False
        self.assertTrue(serializer.is_valid())
        #BUG: Throws AttributeError: 'NoneType' object has no attribute 'name'
        self.assertEquals(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        expected = [
            {'name': u'source-1', 'target': None},
            {'name': u'source-2', 'target': 'target-1'},
            {'name': u'source-3', 'target': None},
        ]
        serializer = NullOKSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)
        serializer = NotRequiredSluggedNullableForeignKeySourceSerializer(queryset)
        self.assertEquals(serializer.data, expected)

