import pytest
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


# --- URL builder helpers ---

def _url(prefix, model_path, pk):
    return '%s/%s/%s/' % (prefix, model_path, pk)


def _m2m_source_url(pk, prefix='http://testserver'):
    return _url(prefix, 'manytomanysource', pk)


def _m2m_target_url(pk, prefix='http://testserver'):
    return _url(prefix, 'manytomanytarget', pk)


def _fk_source_url(pk, prefix='http://testserver'):
    return _url(prefix, 'foreignkeysource', pk)


def _fk_target_url(pk, prefix='http://testserver'):
    return _url(prefix, 'foreignkeytarget', pk)


def _nfk_source_url(pk, prefix='http://testserver'):
    return _url(prefix, 'nullableforeignkeysource', pk)


def _o2o_target_url(pk, prefix='http://testserver'):
    return _url(prefix, 'onetoonetarget', pk)


def _o2o_source_url(pk, prefix='http://testserver'):
    return _url(prefix, 'nullableonetoonesource', pk)


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

        self.targets = list(ManyToManyTarget.objects.order_by('pk'))
        self.sources = list(ManyToManySource.objects.order_by('pk'))
        self.t1, self.t2, self.t3 = self.targets
        self.s1, self.s2, self.s3 = self.sources

    def test_relative_hyperlinks(self):
        queryset = ManyToManySource.objects.order_by('pk')
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': None})
        expected = [
            {'url': _m2m_source_url(self.s1.pk, ''), 'name': 'source-1', 'targets': [_m2m_target_url(self.t1.pk, '')]},
            {'url': _m2m_source_url(self.s2.pk, ''), 'name': 'source-2', 'targets': [_m2m_target_url(self.t1.pk, ''), _m2m_target_url(self.t2.pk, '')]},
            {'url': _m2m_source_url(self.s3.pk, ''), 'name': 'source-3', 'targets': [_m2m_target_url(self.t1.pk, ''), _m2m_target_url(self.t2.pk, ''), _m2m_target_url(self.t3.pk, '')]}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_many_to_many_retrieve(self):
        queryset = ManyToManySource.objects.order_by('pk')
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _m2m_source_url(self.s1.pk), 'name': 'source-1', 'targets': [_m2m_target_url(self.t1.pk)]},
            {'url': _m2m_source_url(self.s2.pk), 'name': 'source-2', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t2.pk)]},
            {'url': _m2m_source_url(self.s3.pk), 'name': 'source-3', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t2.pk), _m2m_target_url(self.t3.pk)]}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_many_to_many_retrieve_prefetch_related(self):
        queryset = ManyToManySource.objects.all().prefetch_related('targets')
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': request})
        with self.assertNumQueries(2):
            serializer.data

    def test_reverse_many_to_many_retrieve(self):
        queryset = ManyToManyTarget.objects.order_by('pk')
        serializer = ManyToManyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _m2m_target_url(self.t1.pk), 'name': 'target-1', 'sources': [_m2m_source_url(self.s1.pk), _m2m_source_url(self.s2.pk), _m2m_source_url(self.s3.pk)]},
            {'url': _m2m_target_url(self.t2.pk), 'name': 'target-2', 'sources': [_m2m_source_url(self.s2.pk), _m2m_source_url(self.s3.pk)]},
            {'url': _m2m_target_url(self.t3.pk), 'name': 'target-3', 'sources': [_m2m_source_url(self.s3.pk)]}
        ]
        with self.assertNumQueries(4):
            assert serializer.data == expected

    def test_many_to_many_update(self):
        data = {'url': _m2m_source_url(self.s1.pk), 'name': 'source-1', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t2.pk), _m2m_target_url(self.t3.pk)]}
        instance = ManyToManySource.objects.get(pk=self.s1.pk)
        serializer = ManyToManySourceSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ManyToManySource.objects.order_by('pk')
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _m2m_source_url(self.s1.pk), 'name': 'source-1', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t2.pk), _m2m_target_url(self.t3.pk)]},
            {'url': _m2m_source_url(self.s2.pk), 'name': 'source-2', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t2.pk)]},
            {'url': _m2m_source_url(self.s3.pk), 'name': 'source-3', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t2.pk), _m2m_target_url(self.t3.pk)]}
        ]
        assert serializer.data == expected

    def test_reverse_many_to_many_update(self):
        data = {'url': _m2m_target_url(self.t1.pk), 'name': 'target-1', 'sources': [_m2m_source_url(self.s1.pk)]}
        instance = ManyToManyTarget.objects.get(pk=self.t1.pk)
        serializer = ManyToManyTargetSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data
        # Ensure target 1 is updated, and everything else is as expected
        queryset = ManyToManyTarget.objects.order_by('pk')
        serializer = ManyToManyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _m2m_target_url(self.t1.pk), 'name': 'target-1', 'sources': [_m2m_source_url(self.s1.pk)]},
            {'url': _m2m_target_url(self.t2.pk), 'name': 'target-2', 'sources': [_m2m_source_url(self.s2.pk), _m2m_source_url(self.s3.pk)]},
            {'url': _m2m_target_url(self.t3.pk), 'name': 'target-3', 'sources': [_m2m_source_url(self.s3.pk)]}

        ]
        assert serializer.data == expected

    def test_many_to_many_create(self):
        data = {'url': 'http://testserver/manytomanysource/999/', 'name': 'source-4', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t3.pk)]}
        serializer = ManyToManySourceSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert obj.name == 'source-4'

        # Ensure source 4 is added, and everything else is as expected
        queryset = ManyToManySource.objects.order_by('pk')
        serializer = ManyToManySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _m2m_source_url(self.s1.pk), 'name': 'source-1', 'targets': [_m2m_target_url(self.t1.pk)]},
            {'url': _m2m_source_url(self.s2.pk), 'name': 'source-2', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t2.pk)]},
            {'url': _m2m_source_url(self.s3.pk), 'name': 'source-3', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t2.pk), _m2m_target_url(self.t3.pk)]},
            {'url': _m2m_source_url(obj.pk), 'name': 'source-4', 'targets': [_m2m_target_url(self.t1.pk), _m2m_target_url(self.t3.pk)]}
        ]
        assert serializer.data == expected

    def test_reverse_many_to_many_create(self):
        data = {'url': 'http://testserver/manytomanytarget/999/', 'name': 'target-4', 'sources': [_m2m_source_url(self.s1.pk), _m2m_source_url(self.s3.pk)]}
        serializer = ManyToManyTargetSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert obj.name == 'target-4'

        # Ensure target 4 is added, and everything else is as expected
        queryset = ManyToManyTarget.objects.order_by('pk')
        serializer = ManyToManyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _m2m_target_url(self.t1.pk), 'name': 'target-1', 'sources': [_m2m_source_url(self.s1.pk), _m2m_source_url(self.s2.pk), _m2m_source_url(self.s3.pk)]},
            {'url': _m2m_target_url(self.t2.pk), 'name': 'target-2', 'sources': [_m2m_source_url(self.s2.pk), _m2m_source_url(self.s3.pk)]},
            {'url': _m2m_target_url(self.t3.pk), 'name': 'target-3', 'sources': [_m2m_source_url(self.s3.pk)]},
            {'url': _m2m_target_url(obj.pk), 'name': 'target-4', 'sources': [_m2m_source_url(self.s1.pk), _m2m_source_url(self.s3.pk)]}
        ]
        assert serializer.data == expected

    def test_data_cannot_be_accessed_prior_to_is_valid(self):
        """Test that .data cannot be accessed prior to .is_valid for hyperlinked serializers."""
        serializer = ManyToManySourceSerializer(
            data={'name': 'test-source', 'targets': [_m2m_target_url(self.t1.pk)]},
            context={'request': request}
        )
        with pytest.raises(AssertionError):
            serializer.data


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

        self.target1 = target
        self.target2 = new_target
        self.sources = list(ForeignKeySource.objects.order_by('pk'))
        self.s1, self.s2, self.s3 = self.sources

    def test_foreign_key_retrieve(self):
        queryset = ForeignKeySource.objects.order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _fk_source_url(self.s1.pk), 'name': 'source-1', 'target': _fk_target_url(self.target1.pk)},
            {'url': _fk_source_url(self.s2.pk), 'name': 'source-2', 'target': _fk_target_url(self.target1.pk)},
            {'url': _fk_source_url(self.s3.pk), 'name': 'source-3', 'target': _fk_target_url(self.target1.pk)}
        ]
        with self.assertNumQueries(1):
            assert serializer.data == expected

    def test_reverse_foreign_key_retrieve(self):
        queryset = ForeignKeyTarget.objects.order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _fk_target_url(self.target1.pk), 'name': 'target-1', 'sources': [_fk_source_url(self.s1.pk), _fk_source_url(self.s2.pk), _fk_source_url(self.s3.pk)]},
            {'url': _fk_target_url(self.target2.pk), 'name': 'target-2', 'sources': []},
        ]
        with self.assertNumQueries(3):
            assert serializer.data == expected

    def test_foreign_key_update(self):
        data = {'url': _fk_source_url(self.s1.pk), 'name': 'source-1', 'target': _fk_target_url(self.target2.pk)}
        instance = ForeignKeySource.objects.get(pk=self.s1.pk)
        serializer = ForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _fk_source_url(self.s1.pk), 'name': 'source-1', 'target': _fk_target_url(self.target2.pk)},
            {'url': _fk_source_url(self.s2.pk), 'name': 'source-2', 'target': _fk_target_url(self.target1.pk)},
            {'url': _fk_source_url(self.s3.pk), 'name': 'source-3', 'target': _fk_target_url(self.target1.pk)}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_incorrect_type(self):
        data = {'url': _fk_source_url(self.s1.pk), 'name': 'source-1', 'target': 2}
        instance = ForeignKeySource.objects.get(pk=self.s1.pk)
        serializer = ForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert not serializer.is_valid()
        assert serializer.errors == {'target': ['Incorrect type. Expected URL string, received int.']}

    def test_reverse_foreign_key_update(self):
        data = {'url': _fk_target_url(self.target2.pk), 'name': 'target-2', 'sources': [_fk_source_url(self.s1.pk), _fk_source_url(self.s3.pk)]}
        instance = ForeignKeyTarget.objects.get(pk=self.target2.pk)
        serializer = ForeignKeyTargetSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        # We shouldn't have saved anything to the db yet since save
        # hasn't been called.
        queryset = ForeignKeyTarget.objects.order_by('pk')
        new_serializer = ForeignKeyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _fk_target_url(self.target1.pk), 'name': 'target-1', 'sources': [_fk_source_url(self.s1.pk), _fk_source_url(self.s2.pk), _fk_source_url(self.s3.pk)]},
            {'url': _fk_target_url(self.target2.pk), 'name': 'target-2', 'sources': []},
        ]
        assert new_serializer.data == expected

        serializer.save()
        assert serializer.data == data

        # Ensure target 2 is update, and everything else is as expected
        queryset = ForeignKeyTarget.objects.order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _fk_target_url(self.target1.pk), 'name': 'target-1', 'sources': [_fk_source_url(self.s2.pk)]},
            {'url': _fk_target_url(self.target2.pk), 'name': 'target-2', 'sources': [_fk_source_url(self.s1.pk), _fk_source_url(self.s3.pk)]},
        ]
        assert serializer.data == expected

    def test_foreign_key_create(self):
        data = {'url': 'http://testserver/foreignkeysource/999/', 'name': 'source-4', 'target': _fk_target_url(self.target2.pk)}
        serializer = ForeignKeySourceSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert obj.name == 'source-4'

        # Ensure source 1 is updated, and everything else is as expected
        queryset = ForeignKeySource.objects.order_by('pk')
        serializer = ForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _fk_source_url(self.s1.pk), 'name': 'source-1', 'target': _fk_target_url(self.target1.pk)},
            {'url': _fk_source_url(self.s2.pk), 'name': 'source-2', 'target': _fk_target_url(self.target1.pk)},
            {'url': _fk_source_url(self.s3.pk), 'name': 'source-3', 'target': _fk_target_url(self.target1.pk)},
            {'url': _fk_source_url(obj.pk), 'name': 'source-4', 'target': _fk_target_url(self.target2.pk)},
        ]
        assert serializer.data == expected

    def test_reverse_foreign_key_create(self):
        data = {'url': 'http://testserver/foreignkeytarget/999/', 'name': 'target-3', 'sources': [_fk_source_url(self.s1.pk), _fk_source_url(self.s3.pk)]}
        serializer = ForeignKeyTargetSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        assert obj.name == 'target-3'

        # Ensure target 4 is added, and everything else is as expected
        queryset = ForeignKeyTarget.objects.order_by('pk')
        serializer = ForeignKeyTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _fk_target_url(self.target1.pk), 'name': 'target-1', 'sources': [_fk_source_url(self.s2.pk)]},
            {'url': _fk_target_url(self.target2.pk), 'name': 'target-2', 'sources': []},
            {'url': _fk_target_url(obj.pk), 'name': 'target-3', 'sources': [_fk_source_url(self.s1.pk), _fk_source_url(self.s3.pk)]},
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_invalid_null(self):
        data = {'url': _fk_source_url(self.s1.pk), 'name': 'source-1', 'target': None}
        instance = ForeignKeySource.objects.get(pk=self.s1.pk)
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

        self.target1 = ForeignKeyTarget.objects.get(name='target-1')
        self.sources = list(NullableForeignKeySource.objects.order_by('pk'))
        self.s1, self.s2, self.s3 = self.sources

    def test_foreign_key_retrieve_with_null(self):
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _nfk_source_url(self.s1.pk), 'name': 'source-1', 'target': _fk_target_url(self.target1.pk)},
            {'url': _nfk_source_url(self.s2.pk), 'name': 'source-2', 'target': _fk_target_url(self.target1.pk)},
            {'url': _nfk_source_url(self.s3.pk), 'name': 'source-3', 'target': None},
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_null(self):
        data = {'url': 'http://testserver/nullableforeignkeysource/999/', 'name': 'source-4', 'target': None}
        serializer = NullableForeignKeySourceSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        expected_data = {'url': _nfk_source_url(obj.pk), 'name': 'source-4', 'target': None}
        assert serializer.data == expected_data
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _nfk_source_url(self.s1.pk), 'name': 'source-1', 'target': _fk_target_url(self.target1.pk)},
            {'url': _nfk_source_url(self.s2.pk), 'name': 'source-2', 'target': _fk_target_url(self.target1.pk)},
            {'url': _nfk_source_url(self.s3.pk), 'name': 'source-3', 'target': None},
            {'url': _nfk_source_url(obj.pk), 'name': 'source-4', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_create_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'url': 'http://testserver/nullableforeignkeysource/999/', 'name': 'source-4', 'target': ''}
        serializer = NullableForeignKeySourceSerializer(data=data, context={'request': request})
        assert serializer.is_valid()
        obj = serializer.save()
        expected_data = {'url': _nfk_source_url(obj.pk), 'name': 'source-4', 'target': None}
        assert serializer.data == expected_data
        assert obj.name == 'source-4'

        # Ensure source 4 is created, and everything else is as expected
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _nfk_source_url(self.s1.pk), 'name': 'source-1', 'target': _fk_target_url(self.target1.pk)},
            {'url': _nfk_source_url(self.s2.pk), 'name': 'source-2', 'target': _fk_target_url(self.target1.pk)},
            {'url': _nfk_source_url(self.s3.pk), 'name': 'source-3', 'target': None},
            {'url': _nfk_source_url(obj.pk), 'name': 'source-4', 'target': None}
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_valid_null(self):
        data = {'url': _nfk_source_url(self.s1.pk), 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=self.s1.pk)
        serializer = NullableForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _nfk_source_url(self.s1.pk), 'name': 'source-1', 'target': None},
            {'url': _nfk_source_url(self.s2.pk), 'name': 'source-2', 'target': _fk_target_url(self.target1.pk)},
            {'url': _nfk_source_url(self.s3.pk), 'name': 'source-3', 'target': None},
        ]
        assert serializer.data == expected

    def test_foreign_key_update_with_valid_emptystring(self):
        """
        The emptystring should be interpreted as null in the context
        of relationships.
        """
        data = {'url': _nfk_source_url(self.s1.pk), 'name': 'source-1', 'target': ''}
        expected_data = {'url': _nfk_source_url(self.s1.pk), 'name': 'source-1', 'target': None}
        instance = NullableForeignKeySource.objects.get(pk=self.s1.pk)
        serializer = NullableForeignKeySourceSerializer(instance, data=data, context={'request': request})
        assert serializer.is_valid()
        serializer.save()
        assert serializer.data == expected_data

        # Ensure source 1 is updated, and everything else is as expected
        queryset = NullableForeignKeySource.objects.order_by('pk')
        serializer = NullableForeignKeySourceSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _nfk_source_url(self.s1.pk), 'name': 'source-1', 'target': None},
            {'url': _nfk_source_url(self.s2.pk), 'name': 'source-2', 'target': _fk_target_url(self.target1.pk)},
            {'url': _nfk_source_url(self.s3.pk), 'name': 'source-3', 'target': None},
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

        self.target1 = target
        self.target2 = new_target
        self.source1 = source

    def test_reverse_foreign_key_retrieve_with_null(self):
        queryset = OneToOneTarget.objects.order_by('pk')
        serializer = NullableOneToOneTargetSerializer(queryset, many=True, context={'request': request})
        expected = [
            {'url': _o2o_target_url(self.target1.pk), 'name': 'target-1', 'nullable_source': _o2o_source_url(self.source1.pk)},
            {'url': _o2o_target_url(self.target2.pk), 'name': 'target-2', 'nullable_source': None},
        ]
        assert serializer.data == expected
