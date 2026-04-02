import uuid

import pytest
from _pytest.monkeypatch import MonkeyPatch
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.test import override_settings
from django.urls import re_path
from django.utils.datastructures import MultiValueDict

from rest_framework import relations, serializers
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


class MockApiSettings:
    def __init__(self, cutoff, cutoff_text):
        self.HTML_SELECT_CUTOFF = cutoff
        self.HTML_SELECT_CUTOFF_TEXT = cutoff_text


class TestRelatedFieldHTMLCutoff(APISimpleTestCase):
    def setUp(self):
        self.queryset = MockQueryset([
            MockObject(pk=i, name=str(i)) for i in range(0, 1100)
        ])
        self.monkeypatch = MonkeyPatch()

    def test_no_settings(self):
        # The default is 1,000, so sans settings it should be 1,000 plus one.
        for many in (False, True):
            field = serializers.PrimaryKeyRelatedField(queryset=self.queryset,
                                                       many=many)
            options = list(field.iter_options())
            assert len(options) == 1001
            assert options[-1].display_text == "More than 1000 items..."

    def test_settings_cutoff(self):
        self.monkeypatch.setattr(relations, "api_settings",
                                 MockApiSettings(2, "Cut Off"))
        for many in (False, True):
            field = serializers.PrimaryKeyRelatedField(queryset=self.queryset,
                                                       many=many)
            options = list(field.iter_options())
            assert len(options) == 3  # 2 real items plus the 'Cut Off' item.
            assert options[-1].display_text == "Cut Off"

    def test_settings_cutoff_none(self):
        # Setting it to None should mean no limit; the default limit is 1,000.
        self.monkeypatch.setattr(relations, "api_settings",
                                 MockApiSettings(None, "Cut Off"))
        for many in (False, True):
            field = serializers.PrimaryKeyRelatedField(queryset=self.queryset,
                                                       many=many)
            options = list(field.iter_options())
            assert len(options) == 1100

    def test_settings_kwargs_cutoff(self):
        # The explicit argument should override the settings.
        self.monkeypatch.setattr(relations, "api_settings",
                                 MockApiSettings(2, "Cut Off"))
        for many in (False, True):
            field = serializers.PrimaryKeyRelatedField(queryset=self.queryset,
                                                       many=many,
                                                       html_cutoff=100)
            options = list(field.iter_options())
            assert len(options) == 101
            assert options[-1].display_text == "Cut Off"


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

    def test_pk_related_lookup_bool(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.field.to_internal_value(True)
        msg = excinfo.value.detail[0]
        assert msg == 'Incorrect type. Expected pk value, received bool.'

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


urlpatterns = [
    re_path(r'^example/(?P<name>.+)/$', lambda: None, name='example'),
]


@override_settings(ROOT_URLCONF='tests.test_relations')
class TestHyperlinkedRelatedField(APISimpleTestCase):
    def setUp(self):
        self.queryset = MockQueryset([
            MockObject(pk=1, name='foobar'),
            MockObject(pk=2, name='bazABCqux'),
            MockObject(pk=2, name='bazABC qux'),
        ])
        self.field = serializers.HyperlinkedRelatedField(
            view_name='example',
            lookup_field='name',
            lookup_url_kwarg='name',
            queryset=self.queryset,
        )
        self.field.reverse = mock_reverse
        self.field._context = {'request': True}

    def test_representation_unsaved_object_with_non_nullable_pk(self):
        representation = self.field.to_representation(MockObject(pk=''))
        assert representation is None

    def test_serialize_empty_relationship_attribute(self):
        class TestSerializer(serializers.Serializer):
            via_unreachable = serializers.HyperlinkedRelatedField(
                source='does_not_exist.unreachable',
                view_name='example',
                read_only=True,
            )

        class TestSerializable:
            @property
            def does_not_exist(self):
                raise ObjectDoesNotExist

        serializer = TestSerializer(TestSerializable())
        assert serializer.data == {'via_unreachable': None}

    def test_hyperlinked_related_lookup_exists(self):
        instance = self.field.to_internal_value('http://example.org/example/foobar/')
        assert instance is self.queryset.items[0]

    def test_hyperlinked_related_lookup_url_encoded_exists(self):
        instance = self.field.to_internal_value('http://example.org/example/baz%41%42%43qux/')
        assert instance is self.queryset.items[1]

    def test_hyperlinked_related_lookup_url_space_encoded_exists(self):
        instance = self.field.to_internal_value('http://example.org/example/bazABC%20qux/')
        assert instance is self.queryset.items[2]

    def test_hyperlinked_related_lookup_does_not_exist(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.field.to_internal_value('http://example.org/example/doesnotexist/')
        msg = excinfo.value.detail[0]
        assert msg == 'Invalid hyperlink - Object does not exist.'

    def test_hyperlinked_related_internal_type_error(self):
        class Field(serializers.HyperlinkedRelatedField):
            def get_object(self, incorrect, signature):
                raise NotImplementedError()

        field = Field(view_name='example', queryset=self.queryset)
        with pytest.raises(TypeError):
            field.to_internal_value('http://example.org/example/doesnotexist/')

    def hyperlinked_related_queryset_error(self, exc_type):
        class QuerySet:
            def get(self, *args, **kwargs):
                raise exc_type

        field = serializers.HyperlinkedRelatedField(
            view_name='example',
            lookup_field='name',
            queryset=QuerySet(),
        )
        with pytest.raises(serializers.ValidationError) as excinfo:
            field.to_internal_value('http://example.org/example/doesnotexist/')
        msg = excinfo.value.detail[0]
        assert msg == 'Invalid hyperlink - Object does not exist.'

    def test_hyperlinked_related_queryset_type_error(self):
        self.hyperlinked_related_queryset_error(TypeError)

    def test_hyperlinked_related_queryset_value_error(self):
        self.hyperlinked_related_queryset_error(ValueError)


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
        the user has misconfigured something, as the URL conf and the
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


class TestNestedSlugRelatedField(APISimpleTestCase):
    def setUp(self):
        self.queryset = MockQueryset([
            MockObject(
                pk=1, name='foo', nested=MockObject(
                    pk=2, name='bar', nested=MockObject(
                        pk=7, name="foobar"
                    )
                )
            ),
            MockObject(
                pk=3, name='hello', nested=MockObject(
                    pk=4, name='world', nested=MockObject(
                        pk=8, name="helloworld"
                    )
                )
            ),
            MockObject(
                pk=5, name='harry', nested=MockObject(
                    pk=6, name='potter', nested=MockObject(
                        pk=9, name="harrypotter"
                    )
                )
            )
        ])
        self.instance = self.queryset.items[2]
        self.field = serializers.SlugRelatedField(
            slug_field='name', queryset=self.queryset
        )
        self.nested_field = serializers.SlugRelatedField(
            slug_field='nested__name', queryset=self.queryset
        )

        self.nested_nested_field = serializers.SlugRelatedField(
            slug_field='nested__nested__name', queryset=self.queryset
        )

    # testing nested inside nested relations
    def test_slug_related_nested_nested_lookup_exists(self):
        instance = self.nested_nested_field.to_internal_value(
            self.instance.nested.nested.name
        )
        assert instance is self.instance

    def test_slug_related_nested_nested_lookup_does_not_exist(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.nested_nested_field.to_internal_value('doesnotexist')
        msg = excinfo.value.detail[0]
        assert msg == \
            'Object with nested__nested__name=doesnotexist does not exist.'

    def test_slug_related_nested_nested_lookup_invalid_type(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.nested_nested_field.to_internal_value(BadType())
        msg = excinfo.value.detail[0]
        assert msg == 'Invalid value.'

    def test_nested_nested_representation(self):
        representation =\
            self.nested_nested_field.to_representation(self.instance)
        assert representation == self.instance.nested.nested.name

    def test_nested_nested_overriding_get_queryset(self):
        qs = self.queryset

        class NoQuerySetSlugRelatedField(serializers.SlugRelatedField):
            def get_queryset(self):
                return qs

        field = NoQuerySetSlugRelatedField(slug_field='nested__nested__name')
        field.to_internal_value(self.instance.nested.nested.name)

    # testing nested relations
    def test_slug_related_nested_lookup_exists(self):
        instance = \
            self.nested_field.to_internal_value(self.instance.nested.name)
        assert instance is self.instance

    def test_slug_related_nested_lookup_does_not_exist(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.nested_field.to_internal_value('doesnotexist')
        msg = excinfo.value.detail[0]
        assert msg == 'Object with nested__name=doesnotexist does not exist.'

    def test_slug_related_nested_lookup_invalid_type(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.nested_field.to_internal_value(BadType())
        msg = excinfo.value.detail[0]
        assert msg == 'Invalid value.'

    def test_nested_representation(self):
        representation = self.nested_field.to_representation(self.instance)
        assert representation == self.instance.nested.name

    def test_nested_overriding_get_queryset(self):
        qs = self.queryset

        class NoQuerySetSlugRelatedField(serializers.SlugRelatedField):
            def get_queryset(self):
                return qs

        field = NoQuerySetSlugRelatedField(slug_field='nested__name')
        field.to_internal_value(self.instance.nested.name)

    # testing non-nested relations
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
    def setup_method(self):
        self.default_hyperlink = serializers.Hyperlink('http://example.com', 'test')

    def test_can_be_pickled(self):
        import pickle
        upkled = pickle.loads(pickle.dumps(self.default_hyperlink))
        assert upkled == self.default_hyperlink
        assert upkled.name == self.default_hyperlink.name
