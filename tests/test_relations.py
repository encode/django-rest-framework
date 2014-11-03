from .utils import mock_reverse, fail_reverse, BadType, MockObject, MockQueryset
from django.core.exceptions import ImproperlyConfigured
from rest_framework import serializers
from rest_framework.test import APISimpleTestCase
import pytest


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
        assert msg == "Invalid pk '4' - object does not exist."

    def test_pk_related_lookup_invalid_type(self):
        with pytest.raises(serializers.ValidationError) as excinfo:
            self.field.to_internal_value(BadType())
        msg = excinfo.value.detail[0]
        assert msg == 'Incorrect type. Expected pk value, received BadType.'

    def test_pk_representation(self):
        representation = self.field.to_representation(self.instance)
        assert representation == self.instance.pk


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

# Older tests, for review...

# """
# General tests for relational fields.
# """
# from __future__ import unicode_literals
# from django import get_version
# from django.db import models
# from django.test import TestCase
# from django.utils import unittest
# from rest_framework import serializers
# from tests.models import BlogPost


# class NullModel(models.Model):
#     pass


# class FieldTests(TestCase):
#     def test_pk_related_field_with_empty_string(self):
#         """
#         Regression test for #446

#         https://github.com/tomchristie/django-rest-framework/issues/446
#         """
#         field = serializers.PrimaryKeyRelatedField(queryset=NullModel.objects.all())
#         self.assertRaises(serializers.ValidationError, field.to_primitive, '')
#         self.assertRaises(serializers.ValidationError, field.to_primitive, [])

#     def test_hyperlinked_related_field_with_empty_string(self):
#         field = serializers.HyperlinkedRelatedField(queryset=NullModel.objects.all(), view_name='')
#         self.assertRaises(serializers.ValidationError, field.to_primitive, '')
#         self.assertRaises(serializers.ValidationError, field.to_primitive, [])

#     def test_slug_related_field_with_empty_string(self):
#         field = serializers.SlugRelatedField(queryset=NullModel.objects.all(), slug_field='pk')
#         self.assertRaises(serializers.ValidationError, field.to_primitive, '')
#         self.assertRaises(serializers.ValidationError, field.to_primitive, [])


# class TestManyRelatedMixin(TestCase):
#     def test_missing_many_to_many_related_field(self):
#         '''
#         Regression test for #632

#         https://github.com/tomchristie/django-rest-framework/pull/632
#         '''
#         field = serializers.RelatedField(many=True, read_only=False)

#         into = {}
#         field.field_from_native({}, None, 'field_name', into)
#         self.assertEqual(into['field_name'], [])


# # Regression tests for #694 (`source` attribute on related fields)

# class RelatedFieldSourceTests(TestCase):
#     def test_related_manager_source(self):
#         """
#         Relational fields should be able to use manager-returning methods as their source.
#         """
#         BlogPost.objects.create(title='blah')
#         field = serializers.RelatedField(many=True, source='get_blogposts_manager')

#         class ClassWithManagerMethod(object):
#             def get_blogposts_manager(self):
#                 return BlogPost.objects

#         obj = ClassWithManagerMethod()
#         value = field.field_to_native(obj, 'field_name')
#         self.assertEqual(value, ['BlogPost object'])

#     def test_related_queryset_source(self):
#         """
#         Relational fields should be able to use queryset-returning methods as their source.
#         """
#         BlogPost.objects.create(title='blah')
#         field = serializers.RelatedField(many=True, source='get_blogposts_queryset')

#         class ClassWithQuerysetMethod(object):
#             def get_blogposts_queryset(self):
#                 return BlogPost.objects.all()

#         obj = ClassWithQuerysetMethod()
#         value = field.field_to_native(obj, 'field_name')
#         self.assertEqual(value, ['BlogPost object'])

#     def test_dotted_source(self):
#         """
#         Source argument should support dotted.source notation.
#         """
#         BlogPost.objects.create(title='blah')
#         field = serializers.RelatedField(many=True, source='a.b.c')

#         class ClassWithQuerysetMethod(object):
#             a = {
#                 'b': {
#                     'c': BlogPost.objects.all()
#                 }
#             }

#         obj = ClassWithQuerysetMethod()
#         value = field.field_to_native(obj, 'field_name')
#         self.assertEqual(value, ['BlogPost object'])

#     # Regression for #1129
#     def test_exception_for_incorect_fk(self):
#         """
#         Check that the exception message are correct if the source field
#         doesn't exist.
#         """
#         from tests.models import ManyToManySource

#         class Meta:
#             model = ManyToManySource

#         attrs = {
#             'name': serializers.SlugRelatedField(
#                 slug_field='name', source='banzai'),
#             'Meta': Meta,
#         }

#         TestSerializer = type(
#             str('TestSerializer'),
#             (serializers.ModelSerializer,),
#             attrs
#         )
#         with self.assertRaises(AttributeError):
#             TestSerializer(data={'name': 'foo'})


# @unittest.skipIf(get_version() < '1.6.0', 'Upstream behaviour changed in v1.6')
# class RelatedFieldChoicesTests(TestCase):
#     """
#     Tests for #1408 "Web browseable API doesn't have blank option on drop down list box"
#     https://github.com/tomchristie/django-rest-framework/issues/1408
#     """
#     def test_blank_option_is_added_to_choice_if_required_equals_false(self):
#         """

#         """
#         post = BlogPost(title="Checking blank option is added")
#         post.save()

#         queryset = BlogPost.objects.all()
#         field = serializers.RelatedField(required=False, queryset=queryset)

#         choice_count = BlogPost.objects.count()
#         widget_count = len(field.widget.choices)

#         self.assertEqual(widget_count, choice_count + 1, 'BLANK_CHOICE_DASH option should have been added')
