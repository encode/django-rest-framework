from django.test import TestCase
from rest_framework import serializers
from rest_framework.compat import patterns, url
from rest_framework.tests.models import ManyToManyTarget, ManyToManySource, ForeignKeyTarget, ForeignKeySource, NullableForeignKeySource, OneToOneTarget, NullableOneToOneSource


def dummy_view(request, pk):
    pass

urlpatterns = patterns('',
    url(r'^manytomanysource/(?P<pk>[0-9]+)/$', dummy_view, name='manytomanysource-detail'),
    url(r'^manytomanytarget/(?P<pk>[0-9]+)/$', dummy_view, name='manytomanytarget-detail'),
    url(r'^foreignkeysource/(?P<pk>[0-9]+)/$', dummy_view, name='foreignkeysource-detail'),
    url(r'^foreignkeytarget/(?P<pk>[0-9]+)/$', dummy_view, name='foreignkeytarget-detail'),
    url(r'^nullableforeignkeysource/(?P<pk>[0-9]+)/$', dummy_view, name='nullableforeignkeysource-detail'),
    url(r'^onetoonetarget/(?P<pk>[0-9]+)/$', dummy_view, name='onetoonetarget-detail'),
    url(r'^nullableonetoonesource/(?P<pk>[0-9]+)/$', dummy_view, name='nullableonetoonesource-detail'),
)


class ManyToManyTargetSerializer(serializers.HyperlinkedModelSerializer):
    sources = serializers.ManyHyperlinkedRelatedField(view_name='manytomanysource-detail')

    class Meta:
        model = ManyToManyTarget


class ManyToManySourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ManyToManySource


class ForeignKeyTargetSerializer(serializers.HyperlinkedModelSerializer):
    sources = serializers.ManyHyperlinkedRelatedField(view_name='foreignkeysource-detail')

    class Meta:
        model = ForeignKeyTarget


class ForeignKeySourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForeignKeySource


# Nullable ForeignKey
class NullableForeignKeySourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NullableForeignKeySource


# OneToOne
class NullableOneToOneTargetSerializer(serializers.HyperlinkedModelSerializer):
    nullable_source = serializers.HyperlinkedRelatedField(view_name='nullableonetoonesource-detail')

    class Meta:
        model = OneToOneTarget


# TODO: Add test that .data cannot be accessed prior to .is_valid

class HyperlinkedManyToManyTests(TestCase):
    urls = 'rest_framework.tests.relations_hyperlink'

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
        serializer = ManyToManySourceSerializer(queryset)
        expected = [
                {'url': '/manytomanysource/1/', 'name': u'source-1', 'targets': ['/manytomanytarget/1/']},
                {'url': '/manytomanysource/2/', 'name': u'source-2', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/']},
                {'url': '/manytomanysource/3/', 'name': u'source-3', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/', '/manytomanytarget/3/']}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_many_to_many_retrieve(self):
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset)
        expected = [
            {'url': '/manytomanytarget/1/', 'name': u'target-1', 'sources': ['/manytomanysource/1/', '/manytomanysource/2/', '/manytomanysource/3/']},
            {'url': '/manytomanytarget/2/', 'name': u'target-2', 'sources': ['/manytomanysource/2/', '/manytomanysource/3/']},
            {'url': '/manytomanytarget/3/', 'name': u'target-3', 'sources': ['/manytomanysource/3/']}
        ]
        self.assertEquals(serializer.data, expected)

    def test_many_to_many_update(self):
        data = {'url': '/manytomanysource/1/', 'name': u'source-1', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/', '/manytomanytarget/3/']}
        instance = ManyToManySource.objects.get(pk=1)
        serializer = ManyToManySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEquals(serializer.data, data)

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset)
        expected = [
                {'url': '/manytomanysource/1/', 'name': u'source-1', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/', '/manytomanytarget/3/']},
                {'url': '/manytomanysource/2/', 'name': u'source-2', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/']},
                {'url': '/manytomanysource/3/', 'name': u'source-3', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/', '/manytomanytarget/3/']}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_many_to_many_update(self):
        data = {'url': '/manytomanytarget/1/', 'name': u'target-1', 'sources': ['/manytomanysource/1/']}
        instance = ManyToManyTarget.objects.get(pk=1)
        serializer = ManyToManyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEquals(serializer.data, data)

        # Ensure target 1 is updated, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset)
        expected = [
            {'url': '/manytomanytarget/1/', 'name': u'target-1', 'sources': ['/manytomanysource/1/']},
            {'url': '/manytomanytarget/2/', 'name': u'target-2', 'sources': ['/manytomanysource/2/', '/manytomanysource/3/']},
            {'url': '/manytomanytarget/3/', 'name': u'target-3', 'sources': ['/manytomanysource/3/']}

        ]
        self.assertEquals(serializer.data, expected)

    def test_many_to_many_create(self):
        data = {'url': '/manytomanysource/4/', 'name': u'source-4', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/3/']}
        serializer = ManyToManySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'source-4')

        # Ensure source 4 is added, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset)
        expected = [
            {'url': '/manytomanysource/1/', 'name': u'source-1', 'targets': ['/manytomanytarget/1/']},
            {'url': '/manytomanysource/2/', 'name': u'source-2', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/']},
            {'url': '/manytomanysource/3/', 'name': u'source-3', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/', '/manytomanytarget/3/']},
            {'url': '/manytomanysource/4/', 'name': u'source-4', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/3/']}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_many_to_many_create(self):
        data = {'url': '/manytomanytarget/4/', 'name': u'target-4', 'sources': ['/manytomanysource/1/', '/manytomanysource/3/']}
        serializer = ManyToManyTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'target-4')

        # Ensure target 4 is added, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset)
        expected = [
            {'url': '/manytomanytarget/1/', 'name': u'target-1', 'sources': ['/manytomanysource/1/', '/manytomanysource/2/', '/manytomanysource/3/']},
            {'url': '/manytomanytarget/2/', 'name': u'target-2', 'sources': ['/manytomanysource/2/', '/manytomanysource/3/']},
            {'url': '/manytomanytarget/3/', 'name': u'target-3', 'sources': ['/manytomanysource/3/']},
            {'url': '/manytomanytarget/4/', 'name': u'target-4', 'sources': ['/manytomanysource/1/', '/manytomanysource/3/']}
        ]
        self.assertEquals(serializer.data, expected)


class HyperlinkedForeignKeyTests(TestCase):
    urls = 'rest_framework.tests.relations_hyperlink'

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
            {'url': '/foreignkeysource/1/', 'name': u'source-1', 'target': '/foreignkeytarget/1/'},
            {'url': '/foreignkeysource/2/', 'name': u'source-2', 'target': '/foreignkeytarget/1/'},
            {'url': '/foreignkeysource/3/', 'name': u'source-3', 'target': '/foreignkeytarget/1/'}
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset)
        expected = [
            {'url': '/foreignkeytarget/1/', 'name': u'target-1', 'sources': ['/foreignkeysource/1/', '/foreignkeysource/2/', '/foreignkeysource/3/']},
            {'url': '/foreignkeytarget/2/', 'name': u'target-2', 'sources': []},
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_update(self):
        data = {'url': '/foreignkeysource/1/', 'name': u'source-1', 'target': '/foreignkeytarget/2/'}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset)
        expected = [
            {'url': '/foreignkeysource/1/', 'name': u'source-1', 'target': '/foreignkeytarget/2/'},
            {'url': '/foreignkeysource/2/', 'name': u'source-2', 'target': '/foreignkeytarget/1/'},
            {'url': '/foreignkeysource/3/', 'name': u'source-3', 'target': '/foreignkeytarget/1/'}
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_update_incorrect_type(self):
        data = {'url': '/foreignkeysource/1/', 'name': u'source-1', 'target': 2}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'target': [u'Incorrect type.  Expected url string, received int.']})

    def test_reverse_foreign_key_update(self):
        data = {'url': '/foreignkeytarget/2/', 'name': u'target-2', 'sources': ['/foreignkeysource/1/', '/foreignkeysource/3/']}
        instance = ForeignKeyTarget.objects.get(pk=2)
        serializer = ForeignKeyTargetSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.all()
        new_serializer = ForeignKeyTargetSerializer(queryset)
        expected = [
            {'url': '/foreignkeytarget/1/', 'name': u'target-1', 'sources': ['/foreignkeysource/1/', '/foreignkeysource/2/', '/foreignkeysource/3/']},
            {'url': '/foreignkeytarget/2/', 'name': u'target-2', 'sources': []},
        ]
        self.assertEquals(new_serializer.data, expected)

        serializer.save()
        self.assertEquals(serializer.data, data)

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset)
        expected = [
            {'url': '/foreignkeytarget/1/', 'name': u'target-1', 'sources': ['/foreignkeysource/2/']},
            {'url': '/foreignkeytarget/2/', 'name': u'target-2', 'sources': ['/foreignkeysource/1/', '/foreignkeysource/3/']},
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_create(self):
        data = {'url': '/foreignkeysource/4/', 'name': u'source-4', 'target': '/foreignkeytarget/2/'}
        serializer = ForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'source-4')

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset)
        expected = [
            {'url': '/foreignkeysource/1/', 'name': u'source-1', 'target': '/foreignkeytarget/1/'},
            {'url': '/foreignkeysource/2/', 'name': u'source-2', 'target': '/foreignkeytarget/1/'},
            {'url': '/foreignkeysource/3/', 'name': u'source-3', 'target': '/foreignkeytarget/1/'},
            {'url': '/foreignkeysource/4/', 'name': u'source-4', 'target': '/foreignkeytarget/2/'},
        ]
        self.assertEquals(serializer.data, expected)

    def test_reverse_foreign_key_create(self):
        data = {'url': '/foreignkeytarget/3/', 'name': u'target-3', 'sources': ['/foreignkeysource/1/', '/foreignkeysource/3/']}
        serializer = ForeignKeyTargetSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'target-3')

        # Ensure target 4 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset)
        expected = [
            {'url': '/foreignkeytarget/1/', 'name': u'target-1', 'sources': ['/foreignkeysource/2/']},
            {'url': '/foreignkeytarget/2/', 'name': u'target-2', 'sources': []},
            {'url': '/foreignkeytarget/3/', 'name': u'target-3', 'sources': ['/foreignkeysource/1/', '/foreignkeysource/3/']},
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_update_with_invalid_null(self):
        data = {'url': '/foreignkeysource/1/', 'name': u'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEquals(serializer.errors, {'target': [u'Value may not be null']})


class HyperlinkedNullableForeignKeyTests(TestCase):
    urls = 'rest_framework.tests.relations_hyperlink'

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
            {'url': '/nullableforeignkeysource/1/', 'name': u'source-1', 'target': '/foreignkeytarget/1/'},
            {'url': '/nullableforeignkeysource/2/', 'name': u'source-2', 'target': '/foreignkeytarget/1/'},
            {'url': '/nullableforeignkeysource/3/', 'name': u'source-3', 'target': None},
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_create_with_valid_null(self):
        data = {'url': '/nullableforeignkeysource/4/', 'name': u'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, data)
        self.assertEqual(obj.name, u'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset)
        expected = [
            {'url': '/nullableforeignkeysource/1/', 'name': u'source-1', 'target': '/foreignkeytarget/1/'},
            {'url': '/nullableforeignkeysource/2/', 'name': u'source-2', 'target': '/foreignkeytarget/1/'},
            {'url': '/nullableforeignkeysource/3/', 'name': u'source-3', 'target': None},
            {'url': '/nullableforeignkeysource/4/', 'name': u'source-4', 'target': None}
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'url': '/nullableforeignkeysource/4/', 'name': u'source-4', 'target': ''}
        expected_data = {'url': '/nullableforeignkeysource/4/', 'name': u'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEquals(serializer.data, expected_data)
        self.assertEqual(obj.name, u'source-4')

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset)
        expected = [
            {'url': '/nullableforeignkeysource/1/', 'name': u'source-1', 'target': '/foreignkeytarget/1/'},
            {'url': '/nullableforeignkeysource/2/', 'name': u'source-2', 'target': '/foreignkeytarget/1/'},
            {'url': '/nullableforeignkeysource/3/', 'name': u'source-3', 'target': None},
            {'url': '/nullableforeignkeysource/4/', 'name': u'source-4', 'target': None}
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_update_with_valid_null(self):
        data = {'url': '/nullableforeignkeysource/1/', 'name': u'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset)
        expected = [
            {'url': '/nullableforeignkeysource/1/', 'name': u'source-1', 'target': None},
            {'url': '/nullableforeignkeysource/2/', 'name': u'source-2', 'target': '/foreignkeytarget/1/'},
            {'url': '/nullableforeignkeysource/3/', 'name': u'source-3', 'target': None},
        ]
        self.assertEquals(serializer.data, expected)

    def test_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'url': '/nullableforeignkeysource/1/', 'name': u'source-1', 'target': ''}
        expected_data = {'url': '/nullableforeignkeysource/1/', 'name': u'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.data, expected_data)
        serializer.save()

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset)
        expected = [
            {'url': '/nullableforeignkeysource/1/', 'name': u'source-1', 'target': None},
            {'url': '/nullableforeignkeysource/2/', 'name': u'source-2', 'target': '/foreignkeytarget/1/'},
            {'url': '/nullableforeignkeysource/3/', 'name': u'source-3', 'target': None},
        ]
        self.assertEquals(serializer.data, expected)

    # reverse foreign keys MUST be read_only
    # In the general case they do not provide .remove() or .clear()
    # and cannot be arbitrarily set.

    # def test_reverse_foreign_key_update(self):
    #     data = {'id': 1, 'name': u'target-1', 'sources': [1]}
    #     instance = ForeignKeyTarget.objects.get(pk=1)
    #     serializer = ForeignKeyTargetSerializer(instance, data=data)
    #     self.assertTrue(serializer.is_valid())
    #     self.assertEquals(serializer.data, data)
    #     serializer.save()

    #     # Ensure target 1 is updated, and everything else is as expected
    #     queryset = ForeignKeyTarget.objects.all()
    #     serializer = ForeignKeyTargetSerializer(queryset)
    #     expected = [
    #         {'id': 1, 'name': u'target-1', 'sources': [1]},
    #         {'id': 2, 'name': u'target-2', 'sources': []},
    #     ]
    #     self.assertEquals(serializer.data, expected)


class HyperlinkedNullableOneToOneTests(TestCase):
    urls = 'rest_framework.tests.relations_hyperlink'

    def setUp(self):
        target = OneToOneTarget(name='target-1')
        target.save()
        new_target = OneToOneTarget(name='target-2')
        new_target.save()
        source = NullableOneToOneSource(name='source-1', target=target)
        source.save()

    def test_reverse_foreign_key_retrieve_with_null(self):
        queryset = OneToOneTarget.objects.all()
        serializer = NullableOneToOneTargetSerializer(queryset)
        expected = [
            {'url': '/onetoonetarget/1/', 'name': u'target-1', 'nullable_source': '/nullableonetoonesource/1/'},
            {'url': '/onetoonetarget/2/', 'name': u'target-2', 'nullable_source': None},
        ]
        self.assertEquals(serializer.data, expected)
