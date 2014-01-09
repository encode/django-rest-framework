"""
General tests for relational fields.
"""
from __future__ import unicode_literals
from django.db import models
from django.test import TestCase
from rest_framework import serializers
from rest_framework.tests.models import BlogPost


class NullModel(models.Model):
    pass


class FieldTests(TestCase):
    def test_pk_related_field_with_empty_string(self):
        """
        Regression test for #446

        https://github.com/tomchristie/django-rest-framework/issues/446
        """
        field = serializers.PrimaryKeyRelatedField(queryset=NullModel.objects.all())
        self.assertRaises(serializers.ValidationError, field.from_native, '')
        self.assertRaises(serializers.ValidationError, field.from_native, [])

    def test_hyperlinked_related_field_with_empty_string(self):
        field = serializers.HyperlinkedRelatedField(queryset=NullModel.objects.all(), view_name='')
        self.assertRaises(serializers.ValidationError, field.from_native, '')
        self.assertRaises(serializers.ValidationError, field.from_native, [])

    def test_slug_related_field_with_empty_string(self):
        field = serializers.SlugRelatedField(queryset=NullModel.objects.all(), slug_field='pk')
        self.assertRaises(serializers.ValidationError, field.from_native, '')
        self.assertRaises(serializers.ValidationError, field.from_native, [])


class TestManyRelatedMixin(TestCase):
    def test_missing_many_to_many_related_field(self):
        '''
        Regression test for #632

        https://github.com/tomchristie/django-rest-framework/pull/632
        '''
        field = serializers.RelatedField(many=True, read_only=False)

        into = {}
        field.field_from_native({}, None, 'field_name', into)
        self.assertEqual(into['field_name'], [])


# Regression tests for #694 (`source` attribute on related fields)

class RelatedFieldSourceTests(TestCase):
    def test_related_manager_source(self):
        """
        Relational fields should be able to use manager-returning methods as their source.
        """
        BlogPost.objects.create(title='blah')
        field = serializers.RelatedField(many=True, source='get_blogposts_manager')

        class ClassWithManagerMethod(object):
            def get_blogposts_manager(self):
                return BlogPost.objects

        obj = ClassWithManagerMethod()
        value = field.field_to_native(obj, 'field_name')
        self.assertEqual(value, ['BlogPost object'])

    def test_related_queryset_source(self):
        """
        Relational fields should be able to use queryset-returning methods as their source.
        """
        BlogPost.objects.create(title='blah')
        field = serializers.RelatedField(many=True, source='get_blogposts_queryset')

        class ClassWithQuerysetMethod(object):
            def get_blogposts_queryset(self):
                return BlogPost.objects.all()

        obj = ClassWithQuerysetMethod()
        value = field.field_to_native(obj, 'field_name')
        self.assertEqual(value, ['BlogPost object'])

    def test_dotted_source(self):
        """
        Source argument should support dotted.source notation.
        """
        BlogPost.objects.create(title='blah')
        field = serializers.RelatedField(many=True, source='a.b.c')

        class ClassWithQuerysetMethod(object):
            a = {
                'b': {
                    'c': BlogPost.objects.all()
                }
            }

        obj = ClassWithQuerysetMethod()
        value = field.field_to_native(obj, 'field_name')
        self.assertEqual(value, ['BlogPost object'])

    # Regression for #1129
    def test_exception_for_incorect_fk(self):
        """
        Check that the exception message are correct if the source field
        doesn't exist.
        """
        from rest_framework.tests.models import ManyToManySource
        class Meta:
            model = ManyToManySource
        attrs = {
            'name': serializers.SlugRelatedField(
                slug_field='name', source='banzai'),
            'Meta': Meta,
        }

        TestSerializer = type(str('TestSerializer'),
            (serializers.ModelSerializer,), attrs)
        with self.assertRaises(AttributeError):
            TestSerializer(data={'name': 'foo'})
