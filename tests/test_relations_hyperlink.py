from django.test import TestCase, override_settings
from django.urls import path

from rest_framework import serializers
from rest_framework.test import APIRequestFactory
from tests.models import (
    ForeignKeySource, ForeignKeyTarget, ManyToManySource, ManyToManyTarget,
    NullableForeignKeySource, NullableOneToOneSource, OneToOneTarget
)

factory = APIRequestFactory()
request = factory.get('/')  # Just to ensure we have a request in the serializer context


def dummy_view(request, pk):
    pass


urlpatterns = [
    path('dummyurl/<int:pk>/', dummy_view, name='dummy-url'),
    path('manytomanysource/<int:pk>/', dummy_view, name='manytomanysource-detail'),
    path('manytomanytarget/<int:pk>/', dummy_view, name='manytomanytarget-detail'),
    path('foreignkeysource/<int:pk>/', dummy_view, name='foreignkeysource-detail'),
    path('foreignkeytarget/<int:pk>/', dummy_view, name='foreignkeytarget-detail'),
    path('nullableforeignkeysource/<int:pk>/', dummy_view, name='nullableforeignkeysource-detail'),
    path('onetoonetarget/<int:pk>/', dummy_view, name='onetoonetarget-detail'),
    path('nullableonetoonesource/<int:pk>/', dummy_view, name='nullableonetoonesource-detail'),
]


# ManyToMany
class ManyToManyTargetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ManyToManyTarget
        fields = ('url', 'name', 'sources')


class ManyToManySourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ManyToManySource
        fields = ('url', 'name', 'targets')


# ForeignKey
class ForeignKeyTargetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForeignKeyTarget
        fields = ('url', 'name', 'sources')


class ForeignKeySourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForeignKeySource
        fields = ('url', 'name', 'target')


# Nullable ForeignKey
class NullableForeignKeySourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = NullableForeignKeySource
        fields = ('url', 'name', 'target')


# Nullable OneToOne
class NullableOneToOneTargetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OneToOneTarget
        fields = ('url', 'name', 'nullable_source')


# TODO: Add test that .data cannot be accessed prior to .is_valid
@override_settings(ROOT_URLCONF='tests.test_relations_hyperlink')
class HyperlinkedManyToManyTests(TestCase):
    def setUp(self):
        for idx in range(1, 4):
            target = ManyToManyTarget(name='target-%d' % idx)
            target.save()
            source = ManyToManySource(name='source-%d' % idx)
            source.save()
            for target in ManyToManyTarget.objects.all():
                source.targets.add(target)

    def test_relative_hyperlinks(self):
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': None})
        expected = [
            {'url': '/manytomanysource/1/', 'name': 'source-1', 'targets': ['/manytomanytarget/1/']},
            {'url': '/manytomanysource/2/', 'name': 'source-2', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/']},
            {'url': '/manytomanysource/3/', 'name': 'source-3', 'targets': ['/manytomanytarget/1/', '/manytomanytarget/2/', '/manytomanytarget/3/']}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_many_to_many_retrieve(self):
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/manytomanysource/1/', 'name': 'source-1', 'targets': ['http://testserver/manytomanytarget/1/']},
            {'url': 'http://testserver/manytomanysource/2/', 'name': 'source-2', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/2/']},
            {'url': 'http://testserver/manytomanysource/3/', 'name': 'source-3', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/2/', 'http://testserver/manytomanytarget/3/']}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_many_to_many_retrieve_prefetch_related(self):
        queryset = ManyToManySource.objects.all().prefetch_related('targets')
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': request})
        with self.assertNumQueries(2):
            serializer.data

    def test_reverse_many_to_many_retrieve(self):
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/manytomanytarget/1/', 'name': 'target-1', 'sources': ['http://testserver/manytomanysource/1/', 'http://testserver/manytomanysource/2/', 'http://testserver/manytomanysource/3/']},
            {'url': 'http://testserver/manytomanytarget/2/', 'name': 'target-2', 'sources': ['http://testserver/manytomanysource/2/', 'http://testserver/manytomanysource/3/']},
            {'url': 'http://testserver/manytomanytarget/3/', 'name': 'target-3', 'sources': ['http://testserver/manytomanysource/3/']}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_many_to_many_update(self):
        data = {'url': 'http://testserver/manytomanysource/1/', 'name': 'source-1', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/2/', 'http://testserver/manytomanytarget/3/']}
        instance = ManyToManySource.objects.get(pk=1)
        serializer = ManyToManySourceSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/manytomanysource/1/', 'name': 'source-1', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/2/', 'http://testserver/manytomanytarget/3/']},
            {'url': 'http://testserver/manytomanysource/2/', 'name': 'source-2', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/2/']},
            {'url': 'http://testserver/manytomanysource/3/', 'name': 'source-3', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/2/', 'http://testserver/manytomanytarget/3/']}
        ]
        assert serializer.data == expected

    def test_reverse_many_to_many_update(self):
        data = {'url': 'http://testserver/manytomanytarget/1/', 'name': 'target-1', 'sources': ['http://testserver/manytomanysource/1/']}
        instance = ManyToManyTarget.objects.get(pk=1)
        serializer = ManyToManyTargetSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data
        # Ensure target 1 is updated, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/manytomanytarget/1/', 'name': 'target-1', 'sources': ['http://testserver/manytomanysource/1/']},
            {'url': 'http://testserver/manytomanytarget/2/', 'name': 'target-2', 'sources': ['http://testserver/manytomanysource/2/', 'http://testserver/manytomanysource/3/']},
            {'url': 'http://testserver/manytomanytarget/3/', 'name': 'target-3', 'sources': ['http://testserver/manytomanysource/3/']}

        ]
        assert serializer.data == expected

    def test_many_to_many_create(self):
        data = {'url': 'http://testserver/manytomanysource/4/', 'name': 'source-4', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/3/']}
        serializer = ManyToManySourceSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == data
        assert obj.name == 'source-4'

        # Ensure source 4 is added, and everything else is as expected
        queryset = ManyToManySource.objects.all()
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/manytomanysource/1/', 'name': 'source-1', 'targets': ['http://testserver/manytomanytarget/1/']},
            {'url': 'http://testserver/manytomanysource/2/', 'name': 'source-2', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/2/']},
            {'url': 'http://testserver/manytomanysource/3/', 'name': 'source-3', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/2/', 'http://testserver/manytomanytarget/3/']},
            {'url': 'http://testserver/manytomanysource/4/', 'name': 'source-4', 'targets': ['http://testserver/manytomanytarget/1/', 'http://testserver/manytomanytarget/3/']}
        ]
        assert serializer.data == expected

    def test_reverse_many_to_many_create(self):
        data = {'url': 'http://testserver/manytomanytarget/4/', 'name': 'target-4', 'sources': ['http://testserver/manytomanysource/1/', 'http://testserver/manytomanysource/3/']}
        serializer = ManyToManyTargetSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == data
        assert obj.name == 'target-4'

        # Ensure target 4 is added, and everything else is as expected
        queryset = ManyToManyTarget.objects.all()
        serializer = ManyToManyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/manytomanytarget/1/', 'name': 'target-1', 'sources': ['http://testserver/manytomanysource/1/', 'http://testserver/manytomanysource/2/', 'http://testserver/manytomanysource/3/']},
            {'url': 'http://testserver/manytomanytarget/2/', 'name': 'target-2', 'sources': ['http://testserver/manytomanysource/2/', 'http://testserver/manytomanysource/3/']},
            {'url': 'http://testserver/manytomanytarget/3/', 'name': 'target-3', 'sources': ['http://testserver/manytomanysource/3/']},
            {'url': 'http://testserver/manytomanytarget/4/', 'name': 'target-4', 'sources': ['http://testserver/manytomanysource/1/', 'http://testserver/manytomanysource/3/']}
        ]
        assert serializer.data == expected


@override_settings(ROOT_URLCONF='tests.test_relations_hyperlink')
class HyperlinkedForeignKeyTests(TestCase):
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
        serializer = ForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/foreignkeysource/1/', 'name': 'source-1', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/foreignkeysource/2/', 'name': 'source-2', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/foreignkeysource/3/', 'name': 'source-3', 'target': 'http://testserver/foreignkeytarget/1/'}
        ]
        with self.assertNumQueries(1):
            assert serializer.data == expected

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/foreignkeytarget/1/', 'name': 'target-1', 'sources': ['http://testserver/foreignkeysource/1/', 'http://testserver/foreignkeysource/2/', 'http://testserver/foreignkeysource/3/']},
            {'url': 'http://testserver/foreignkeytarget/2/', 'name': 'target-2', 'sources': []},
        ]
        with self.assertNumQueries(3):
            assert serializer.data == expected

    def test_foreign_key_update(self):
        data = {'url': 'http://testserver/foreignkeysource/1/', 'name': 'source-1', 'target': 'http://testserver/foreignkeytarget/2/'}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/foreignkeysource/1/', 'name': 'source-1', 'target': 'http://testserver/foreignkeytarget/2/'},
            {'url': 'http://testserver/foreignkeysource/2/', 'name': 'source-2', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/foreignkeysource/3/', 'name': 'source-3', 'target': 'http://testserver/foreignkeytarget/1/'}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_incorrect_type(self):
        data = {'url': 'http://testserver/foreignkeysource/1/', 'name': 'source-1', 'target': 2}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['Incorrect type. Expected URL string, received int.']}

    def test_reverse_foreign_key_update(self):
        data = {'url': 'http://testserver/foreignkeytarget/2/', 'name': 'target-2', 'sources': ['http://testserver/foreignkeysource/1/', 'http://testserver/foreignkeysource/3/']}
        instance = ForeignKeyTarget.objects.get(pk=2)
        serializer = ForeignKeyTargetSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.all()
        new_serializer = ForeignKeyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/foreignkeytarget/1/', 'name': 'target-1', 'sources': ['http://testserver/foreignkeysource/1/', 'http://testserver/foreignkeysource/2/', 'http://testserver/foreignkeysource/3/']},
            {'url': 'http://testserver/foreignkeytarget/2/', 'name': 'target-2', 'sources': []},
        ]
        assert new_serializer.data == expected

        serializer.save()
        assert serializer.data == data

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/foreignkeytarget/1/', 'name': 'target-1', 'sources': ['http://testserver/foreignkeysource/2/']},
            {'url': 'http://testserver/foreignkeytarget/2/', 'name': 'target-2', 'sources': ['http://testserver/foreignkeysource/1/', 'http://testserver/foreignkeysource/3/']},
        ]
        assert serializer.data == expected

    def test_foreign_key_create(self):
        data = {'url': 'http://testserver/foreignkeysource/4/', 'name': 'source-4', 'target': 'http://testserver/foreignkeytarget/2/'}
        serializer = ForeignKeySourceSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == data
        assert obj.name == 'source-4'

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.all()
        serializer = ForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/foreignkeysource/1/', 'name': 'source-1', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/foreignkeysource/2/', 'name': 'source-2', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/foreignkeysource/3/', 'name': 'source-3', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/foreignkeysource/4/', 'name': 'source-4', 'target': 'http://testserver/foreignkeytarget/2/'},
        ]
        assert serializer.data == expected

    def test_reverse_foreign_key_create(self):
        data = {'url': 'http://testserver/foreignkeytarget/3/', 'name': 'target-3', 'sources': ['http://testserver/foreignkeysource/1/', 'http://testserver/foreignkeysource/3/']}
        serializer = ForeignKeyTargetSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == data
        assert obj.name == 'target-3'

        # Ensure target 4 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.all()
        serializer = ForeignKeyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/foreignkeytarget/1/', 'name': 'target-1', 'sources': ['http://testserver/foreignkeysource/2/']},
            {'url': 'http://testserver/foreignkeytarget/2/', 'name': 'target-2', 'sources': []},
            {'url': 'http://testserver/foreignkeytarget/3/', 'name': 'target-3', 'sources': ['http://testserver/foreignkeysource/1/', 'http://testserver/foreignkeysource/3/']},
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_invalid_null(self):
        data = {'url': 'http://testserver/foreignkeysource/1/', 'name': 'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=1)
        serializer = ForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['This field may not be null.']}


@override_settings(ROOT_URLCONF='tests.test_relations_hyperlink')
class HyperlinkedNullableForeignKeyTests(TestCase):
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
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/nullableforeignkeysource/1/', 'name': 'source-1', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/nullableforeignkeysource/2/', 'name': 'source-2', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/nullableforeignkeysource/3/', 'name': 'source-3', 'target': None},
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_null(self):
        data = {'url': 'http://testserver/nullableforeignkeysource/4/', 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == data
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/nullableforeignkeysource/1/', 'name': 'source-1', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/nullableforeignkeysource/2/', 'name': 'source-2', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/nullableforeignkeysource/3/', 'name': 'source-3', 'target': None},
            {'url': 'http://testserver/nullableforeignkeysource/4/', 'name': 'source-4', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'url': 'http://testserver/nullableforeignkeysource/4/', 'name': 'source-4', 'target': ''}
        expected_data = {'url': 'http://testserver/nullableforeignkeysource/4/', 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert serializer.data == expected_data
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/nullableforeignkeysource/1/', 'name': 'source-1', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/nullableforeignkeysource/2/', 'name': 'source-2', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/nullableforeignkeysource/3/', 'name': 'source-3', 'target': None},
            {'url': 'http://testserver/nullableforeignkeysource/4/', 'name': 'source-4', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_valid_null(self):
        data = {'url': 'http://testserver/nullableforeignkeysource/1/', 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/nullableforeignkeysource/1/', 'name': 'source-1', 'target': None},
            {'url': 'http://testserver/nullableforeignkeysource/2/', 'name': 'source-2', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/nullableforeignkeysource/3/', 'name': 'source-3', 'target': None},
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'url': 'http://testserver/nullableforeignkeysource/1/', 'name': 'source-1', 'target': ''}
        expected_data = {'url': 'http://testserver/nullableforeignkeysource/1/', 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=1)
        serializer = NullableForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == expected_data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.all()
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/nullableforeignkeysource/1/', 'name': 'source-1', 'target': None},
            {'url': 'http://testserver/nullableforeignkeysource/2/', 'name': 'source-2', 'target': 'http://testserver/foreignkeytarget/1/'},
            {'url': 'http://testserver/nullableforeignkeysource/3/', 'name': 'source-3', 'target': None},
        ]
        assert serializer.data == expected


@override_settings(ROOT_URLCONF='tests.test_relations_hyperlink')
class HyperlinkedNullableOneToOneTests(TestCase):
    def setUp(self):
        target = OneToOneTarget(name='target-1')
        target.save()
        new_target = OneToOneTarget(name='target-2')
        new_target.save()
        source = NullableOneToOneSource(name='source-1', target=target)
        source.save()

    def test_reverse_foreign_key_retrieve_with_null(self):
        queryset = OneToOneTarget.objects.all()
        serializer = NullableOneToOneTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': 'http://testserver/onetoonetarget/1/', 'name': 'target-1', 'nullable_source': 'http://testserver/nullableonetoonesource/1/'},
            {'url': 'http://testserver/onetoonetarget/2/', 'name': 'target-2', 'nullable_source': None},
        ]
        assert serializer.data == expected
