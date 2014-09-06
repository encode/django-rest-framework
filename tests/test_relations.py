"""
General tests for relational fields.
"""
from __future__ import unicode_literals
from django import get_version
from django.db import models
from django.test import TestCase
from django.utils import unittest
from rest_framework import serializers
from tests.models import BlogPost, LimitedChoicesModel, ForeignKeyTarget


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
        from tests.models import ManyToManySource

        class Meta:
            model = ManyToManySource

        attrs = {
            'name': serializers.SlugRelatedField(
                slug_field='name', source='banzai'),
            'Meta': Meta,
        }

        TestSerializer = type(
            str('TestSerializer'),
            (serializers.ModelSerializer,),
            attrs
        )
        with self.assertRaises(AttributeError):
            TestSerializer(data={'name': 'foo'})


@unittest.skipIf(get_version() < '1.6.0', 'Upstream behaviour changed in v1.6')
class RelatedFieldChoicesTests(TestCase):
    """
    Tests for #1408 "Web browseable API doesn't have blank option on drop down list box"
    https://github.com/tomchristie/django-rest-framework/issues/1408
    """
    def test_blank_option_is_added_to_choice_if_required_equals_false(self):
        """

        """
        post = BlogPost(title="Checking blank option is added")
        post.save()

        queryset = BlogPost.objects.all()
        field = serializers.RelatedField(required=False, queryset=queryset)

        choice_count = BlogPost.objects.count()
        widget_count = len(field.widget.choices)

        self.assertEqual(widget_count, choice_count + 1, 'BLANK_CHOICE_DASH option should have been added')


class LimitChoicesToTest(TestCase):
    """
    Test for #1811 "Support `limit_choices_to` on related fields."

    1. Fully auto-generated relation field: should limit if model field has
    limit_choices_to set
    2. Declared relation field with neither queryset or limit_choices_to field
    set: should limit if model field has limit_choices_to set
    3. Declared relation field with queryset declared and without
    limit_choices_to set where the model field has limit_choices_to set: The
    user has explicitly declared a queryset so I don't think we should modify
    it.
    4. Declared relation field with limit_choices_to declared and no queryset
    declared: Should limit choices based on the limit_choices_to that was
    declared on the serializer field.
    5. Declared relation field with both limit_choices_to and queryset
    declared: I think that since both were declared, that it makes sense to go
    ahead and apply the limit choices to filtering to the provided queryset.
    """
    def test_generated_field_with_limit_choices_set_on_model_field(self):
        """
        Ensure that for a fully auto-generated serializer field for a model
        field which has the `limit_choices_to` value set that the queryset is
        filtered correctly on the value from the model field.
        """
        # Generate one instance that will match the `limit_choices_to`
        ForeignKeyTarget.objects.create(name='foo')
        ForeignKeyTarget.objects.create(name='bar')

        class LimitChoicesSerializer(serializers.ModelSerializer):
            class Meta:
                model = LimitedChoicesModel
                fields = ('rel',)

        serializer = LimitChoicesSerializer()

        field = serializer.fields['rel']
        queryset = field.queryset

        self.assertEqual(
            set(queryset.all()),
            set(ForeignKeyTarget.objects.filter(name='foo')),
        )

    def test_declared_related_field_with_limit_choices_set_on_model(self):
        """
        Test that a declared `RelatedField` will correctly filter on it's model
        field's `limit_choices_to` when neither the queryset nor the local
        `limit_choices_to` has been declared.

        TODO: is this test necessary?
        """
        # Generate one instance that will match the `limit_choices_to`
        ForeignKeyTarget.objects.create(name='foo')
        ForeignKeyTarget.objects.create(name='bar')

        class LimitChoicesSerializer(serializers.ModelSerializer):
            rel = serializers.RelatedField(read_only=False)

            class Meta:
                model = LimitedChoicesModel
                fields = ('rel',)

        serializer = LimitChoicesSerializer()

        field = serializer.fields['rel']
        queryset = field.queryset

        self.assertEqual(
            set(queryset.all()),
            set(ForeignKeyTarget.objects.filter(name='foo')),
        )

    def test_declared_queryset_on_related_field_is_not_effected_by_model_limit_choices_to(self):
        """
        Test that when the `queryset` kwarg is declared for a `RelatedField`
        that it isn't further filtered when `limit_choices_to` has been
        declared on the model field.
        """
        ForeignKeyTarget.objects.create(name='foo')
        ForeignKeyTarget.objects.create(name='bar')

        class LimitChoicesSerializer(serializers.ModelSerializer):
            rel = serializers.RelatedField(
                queryset=ForeignKeyTarget.objects.all(),
                read_only=False,
            )

            class Meta:
                model = LimitedChoicesModel
                fields = ('rel',)

        serializer = LimitChoicesSerializer()

        field = serializer.fields['rel']
        queryset = field.queryset

        self.assertEqual(
            set(queryset.all()),
            set(ForeignKeyTarget.objects.all()),
        )

    def test_limit_choices_to_on_serializer_field_overrides_model_field(self):
        """
        Test that when `limit_choices_to` is declared on a serializer field
        that it correctly overrides the value declared on the model field.
        """
        ForeignKeyTarget.objects.create(name='foo')
        ForeignKeyTarget.objects.create(name='bar')

        class LimitChoicesSerializer(serializers.ModelSerializer):
            rel = serializers.RelatedField(limit_choices_to={'name': 'bar'}, read_only=False)

            class Meta:
                model = LimitedChoicesModel
                fields = ('rel',)

        serializer = LimitChoicesSerializer()

        field = serializer.fields['rel']
        queryset = field.queryset

        self.assertEqual(
            set(queryset.all()),
            set(ForeignKeyTarget.objects.filter(name='bar')),
        )

    def test_serializer_field_with_both_limit_choices_to_and_queryset_is_filtered(self):
        """
        Test that when both the `limit_choices_to` and `queryset` are declared
        for a serializer field that the provided queryset is subsequently
        filtered using the provided `limit_choices_to`.
        """
        ForeignKeyTarget.objects.create(name='foo')
        only_choice = ForeignKeyTarget.objects.create(name='bar')
        ForeignKeyTarget.objects.create(name='baz')
        to_exclude = ForeignKeyTarget.objects.create(name='bar')

        class LimitChoicesSerializer(serializers.ModelSerializer):
            rel = serializers.RelatedField(
                limit_choices_to={'name': 'bar'},
                queryset=ForeignKeyTarget.objects.exclude(pk=to_exclude.pk),
                read_only=False,
            )

            class Meta:
                model = LimitedChoicesModel
                fields = ('rel',)

        serializer = LimitChoicesSerializer()

        field = serializer.fields['rel']
        queryset = field.queryset

        self.assertEqual(
            set(queryset.all()),
            set(ForeignKeyTarget.objects.filter(pk=only_choice.pk)),
        )
