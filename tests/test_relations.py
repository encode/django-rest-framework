import uuid

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.utils.datastructures import MultiValueDict

from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.test import APISimpleTestCase

from .utils import (
    BadType, MockObject, MockQueryset, fail_reverse, mock_reverse
)


class TestStringRelatedField(APISimpleTestCase):
    def setUp(self):
        self.instance = MockObject(pk=1, name='foo')
        self.field = serializers.StringRelatedField()

    def test_string_related_representation(self):
        representation = self.field.to_representation(self.instance)
        assert representation == '<MockObject name=foo, pk=1>'


class TestPrimaryKeyRelatedField(APISimpleTestCase):
    def setUp(self):
        self.queryset = MockQueryset([
            MockObject(pk=1, name='foo'),
            MockObject(pk=2, name='bar'),
            MockObject(pk=3, name='baz')
        ])
        self.instance = self.queryset.items[2]
        self.field = serializers.PrimaryKeyRelatedField(queryset=self.queryset)

    def test_pk_related_lookup_exists(self):
        instance = self.field.to_internal_value(self.instance.pk)
        assert instance is self.instance

    def test_pk_related_lookup_does_not_exist(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.field.to_internal_value(4)
        msg = excinfo.value.detail[0]
        assert msg == 'Invalid pk "4" - object does not exist.'

    def test_pk_related_lookup_invalid_type(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.field.to_internal_value(BadType())
        msg = excinfo.value.detail[0]
        assert msg == 'Incorrect type. Expected pk value, received BadType.'

    def test_pk_representation(self):
        representation = self.field.to_representation(self.instance)
        assert representation == self.instance.pk

    def test_explicit_many_false(self):
        field = serializers.PrimaryKeyRelatedField(queryset=self.queryset, many=False)
        instance = field.to_internal_value(self.instance.pk)
        assert instance is self.instance


class TestProxiedPrimaryKeyRelatedField(APISimpleTestCase):
    def setUp(self):
        self.queryset = MockQueryset([
            MockObject(pk=uuid.UUID(int=0), name='foo'),
            MockObject(pk=uuid.UUID(int=1), name='bar'),
            MockObject(pk=uuid.UUID(int=2), name='baz')
        ])
        self.instance = self.queryset.items[2]
        self.field = serializers.PrimaryKeyRelatedField(
            queryset=self.queryset,
            pk_field=serializers.UUIDField(format='int')
        )

    def test_pk_related_lookup_exists(self):
        instance = self.field.to_internal_value(self.instance.pk.int)
        assert instance is self.instance

    def test_pk_related_lookup_does_not_exist(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.field.to_internal_value(4)
        msg = excinfo.value.detail[0]
        assert msg == 'Invalid pk "00000000-0000-0000-0000-000000000004" - object does not exist.'

    def test_pk_representation(self):
        representation = self.field.to_representation(self.instance)
        assert representation == self.instance.pk.int


class TestHyperlinkedRelatedField(APISimpleTestCase):
    def setUp(self):
        self.field = serializers.HyperlinkedRelatedField(
            view_name='example', read_only=True)
        self.field.reverse = mock_reverse
        self.field._context = {'request': True}

    def test_representation_unsaved_object_with_non_nullable_pk(self):
        representation = self.field.to_representation(MockObject(pk=''))
        assert representation is None


class TestHyperlinkedIdentityField(APISimpleTestCase):
    def setUp(self):
        self.instance = MockObject(pk=1, name='foo')
        self.field = serializers.HyperlinkedIdentityField(view_name='example')
        self.field.reverse = mock_reverse
        self.field._context = {'request': True}

    def test_representation(self):
        representation = self.field.to_representation(self.instance)
        assert representation == 'http://example.org/example/1/'

    def test_representation_unsaved_object(self):
        representation = self.field.to_representation(MockObject(pk=None))
        assert representation is None

    def test_representation_with_format(self):
        self.field._context['format'] = 'xml'
        representation = self.field.to_representation(self.instance)
        assert representation == 'http://example.org/example/1.xml/'

    def test_improperly_configured(self):
        """
        If a matching view cannot be reversed with the given instance,
        the the user has misconfigured something, as the URL conf and the
        hyperlinked field do not match.
        """
        self.field.reverse = fail_reverse
        with pytest.raises(ImproperlyConfigured):
            self.field.to_representation(self.instance)


class TestHyperlinkedIdentityFieldWithFormat(APISimpleTestCase):
    """
    Tests for a hyperlinked identity field that has a `format` set,
    which enforces that alternate formats are never linked too.

    Eg. If your API includes some endpoints that accept both `.xml` and `.json`,
    but other endpoints that only accept `.json`, we allow for hyperlinked
    relationships that enforce only a single suffix type.
    """

    def setUp(self):
        self.instance = MockObject(pk=1, name='foo')
        self.field = serializers.HyperlinkedIdentityField(view_name='example', format='json')
        self.field.reverse = mock_reverse
        self.field._context = {'request': True}

    def test_representation(self):
        representation = self.field.to_representation(self.instance)
        assert representation == 'http://example.org/example/1/'

    def test_representation_with_format(self):
        self.field._context['format'] = 'xml'
        representation = self.field.to_representation(self.instance)
        assert representation == 'http://example.org/example/1.json/'


class TestSlugRelatedField(APISimpleTestCase):
    def setUp(self):
        self.queryset = MockQueryset([
            MockObject(pk=1, name='foo'),
            MockObject(pk=2, name='bar'),
            MockObject(pk=3, name='baz')
        ])
        self.instance = self.queryset.items[2]
        self.field = serializers.SlugRelatedField(
            slug_field='name', queryset=self.queryset
        )

    def test_slug_related_lookup_exists(self):
        instance = self.field.to_internal_value(self.instance.name)
        assert instance is self.instance

    def test_slug_related_lookup_does_not_exist(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.field.to_internal_value('doesnotexist')
        msg = excinfo.value.detail[0]
        assert msg == 'Object with name=doesnotexist does not exist.'

    def test_slug_related_lookup_invalid_type(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.field.to_internal_value(BadType())
        msg = excinfo.value.detail[0]
        assert msg == 'Invalid value.'

    def test_representation(self):
        representation = self.field.to_representation(self.instance)
        assert representation == self.instance.name

    def test_overriding_get_queryset(self):
        qs = self.queryset

        class NoQuerySetSlugRelatedField(serializers.SlugRelatedField):
            def get_queryset(self):
                return qs

        field = NoQuerySetSlugRelatedField(slug_field='name')
        field.to_internal_value(self.instance.name)


class TestManyRelatedField(APISimpleTestCase):
    def setUp(self):
        self.instance = MockObject(pk=1, name='foo')
        self.field = serializers.StringRelatedField(many=True)
        self.field.field_name = 'foo'

    def test_get_value_regular_dictionary_full(self):
        assert 'bar' == self.field.get_value({'foo': 'bar'})
        assert empty == self.field.get_value({'baz': 'bar'})

    def test_get_value_regular_dictionary_partial(self):
        setattr(self.field.root, 'partial', True)
        assert 'bar' == self.field.get_value({'foo': 'bar'})
        assert empty == self.field.get_value({'baz': 'bar'})

    def test_get_value_multi_dictionary_full(self):
        mvd = MultiValueDict({'foo': ['bar1', 'bar2']})
        assert ['bar1', 'bar2'] == self.field.get_value(mvd)

        mvd = MultiValueDict({'baz': ['bar1', 'bar2']})
        assert [] == self.field.get_value(mvd)

    def test_get_value_multi_dictionary_partial(self):
        setattr(self.field.root, 'partial', True)
        mvd = MultiValueDict({'foo': ['bar1', 'bar2']})
        assert ['bar1', 'bar2'] == self.field.get_value(mvd)

        mvd = MultiValueDict({'baz': ['bar1', 'bar2']})
        assert empty == self.field.get_value(mvd)


class TestHyperlink:
    def setup(self):
        self.default_hyperlink = serializers.Hyperlink('http://example.com', 'test')

    def test_can_be_pickled(self):
        import pickle
        upkled = pickle.loads(pickle.dumps(self.default_hyperlink))
        assert upkled == self.default_hyperlink
        assert upkled.name == self.default_hyperlink.name
