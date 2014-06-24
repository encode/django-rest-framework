# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
from django.test import TestCase
from django.utils import unittest
from django.utils.datastructures import MultiValueDict
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, fields, relations
from tests.models import (HasPositiveIntegerAsChoice, Album, ActionItem, Anchor, BasicModel,
    BlankFieldModel, BlogPost, BlogPostComment, Book, CallableDefaultValueModel, DefaultValueModel,
    ManyToManyModel, Person, ReadOnlyManyToManyModel, Photo, RESTFrameworkModel,
    ForeignKeySource, ManyToManySource)
from tests.models import BasicModelSerializer
import datetime
import pickle
try:
    import PIL
except:
    PIL = None


if PIL is not None:
    class AMOAFModel(RESTFrameworkModel):
        char_field = models.CharField(max_length=1024, blank=True)
        comma_separated_integer_field = models.CommaSeparatedIntegerField(max_length=1024, blank=True)
        decimal_field = models.DecimalField(max_digits=64, decimal_places=32, blank=True)
        email_field = models.EmailField(max_length=1024, blank=True)
        file_field = models.FileField(upload_to='test', max_length=1024, blank=True)
        image_field = models.ImageField(upload_to='test', max_length=1024, blank=True)
        slug_field = models.SlugField(max_length=1024, blank=True)
        url_field = models.URLField(max_length=1024, blank=True)
        nullable_char_field = models.CharField(max_length=1024, blank=True, null=True)

    class DVOAFModel(RESTFrameworkModel):
        positive_integer_field = models.PositiveIntegerField(blank=True)
        positive_small_integer_field = models.PositiveSmallIntegerField(blank=True)
        email_field = models.EmailField(blank=True)
        file_field = models.FileField(upload_to='test', blank=True)
        image_field = models.ImageField(upload_to='test', blank=True)
        slug_field = models.SlugField(blank=True)
        url_field = models.URLField(blank=True)


class SubComment(object):
    def __init__(self, sub_comment):
        self.sub_comment = sub_comment


class Comment(object):
    def __init__(self, email, content, created):
        self.email = email
        self.content = content
        self.created = created or datetime.datetime.now()

    def __eq__(self, other):
        return all([getattr(self, attr) == getattr(other, attr)
                    for attr in ('email', 'content', 'created')])

    def get_sub_comment(self):
        sub_comment = SubComment('And Merry Christmas!')
        return sub_comment


class CommentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = serializers.CharField(max_length=1000)
    created = serializers.DateTimeField()
    sub_comment = serializers.Field(source='get_sub_comment.sub_comment')

    def restore_object(self, data, instance=None):
        if instance is None:
            return Comment(**data)
        for key, val in data.items():
            setattr(instance, key, val)
        return instance


class NamesSerializer(serializers.Serializer):
    first = serializers.CharField()
    last = serializers.CharField(required=False, default='')
    initials = serializers.CharField(required=False, default='')


class PersonIdentifierSerializer(serializers.Serializer):
    ssn = serializers.CharField()
    names = NamesSerializer(source='names', required=False)


class BookSerializer(serializers.ModelSerializer):
    isbn = serializers.RegexField(regex=r'^[0-9]{13}$', error_messages={'invalid': 'isbn has to be exact 13 numbers'})

    class Meta:
        model = Book


class ActionItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = ActionItem

class ActionItemSerializerOptionalFields(serializers.ModelSerializer):
    """
    Intended to test that fields with `required=False` are excluded from validation.
    """
    title = serializers.CharField(required=False)

    class Meta:
        model = ActionItem
        fields = ('title',)

class ActionItemSerializerCustomRestore(serializers.ModelSerializer):

    class Meta:
        model = ActionItem

    def restore_object(self, data, instance=None):
        if instance is None:
            return ActionItem(**data)
        for key, val in data.items():
            setattr(instance, key, val)
        return instance


class PersonSerializer(serializers.ModelSerializer):
    info = serializers.Field(source='info')

    class Meta:
        model = Person
        fields = ('name', 'age', 'info')
        read_only_fields = ('age',)


class NestedSerializer(serializers.Serializer):
    info = serializers.Field()


class ModelSerializerWithNestedSerializer(serializers.ModelSerializer):
    nested = NestedSerializer(source='*')

    class Meta:
        model = Person


class NestedSerializerWithRenamedField(serializers.Serializer):
    renamed_info = serializers.Field(source='info')


class ModelSerializerWithNestedSerializerWithRenamedField(serializers.ModelSerializer):
    nested = NestedSerializerWithRenamedField(source='*')

    class Meta:
        model = Person


class PersonSerializerInvalidReadOnly(serializers.ModelSerializer):
    """
    Testing for #652.
    """
    info = serializers.Field(source='info')

    class Meta:
        model = Person
        fields = ('name', 'age', 'info')
        read_only_fields = ('age', 'info')


class AlbumsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Album
        fields = ['title', 'ref']  # lists are also valid options


class PositiveIntegerAsChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HasPositiveIntegerAsChoice
        fields = ['some_integer']


class ForeignKeySourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySource


class HyperlinkedForeignKeySourceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ForeignKeySource


class BasicTests(TestCase):
    def setUp(self):
        self.comment = Comment(
            'tom@example.com',
            'Happy new year!',
            datetime.datetime(2012, 1, 1)
        )
        self.actionitem = ActionItem(title='Some to do item',)
        self.data = {
            'email': 'tom@example.com',
            'content': 'Happy new year!',
            'created': datetime.datetime(2012, 1, 1),
            'sub_comment': 'This wont change'
        }
        self.expected = {
            'email': 'tom@example.com',
            'content': 'Happy new year!',
            'created': datetime.datetime(2012, 1, 1),
            'sub_comment': 'And Merry Christmas!'
        }
        self.person_data = {'name': 'dwight', 'age': 35}
        self.person = Person(**self.person_data)
        self.person.save()

    def test_empty(self):
        serializer = CommentSerializer()
        expected = {
            'email': '',
            'content': '',
            'created': None
        }
        self.assertEqual(serializer.data, expected)

    def test_retrieve(self):
        serializer = CommentSerializer(self.comment)
        self.assertEqual(serializer.data, self.expected)

    def test_create(self):
        serializer = CommentSerializer(data=self.data)
        expected = self.comment
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, expected)
        self.assertFalse(serializer.object is expected)
        self.assertEqual(serializer.data['sub_comment'], 'And Merry Christmas!')

    def test_create_nested(self):
        """Test a serializer with nested data."""
        names = {'first': 'John', 'last': 'Doe', 'initials': 'jd'}
        data = {'ssn': '1234567890', 'names': names}
        serializer = PersonIdentifierSerializer(data=data)

        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, data)
        self.assertFalse(serializer.object is data)
        self.assertEqual(serializer.data['names'], names)

    def test_create_partial_nested(self):
        """Test a serializer with nested data which has missing fields."""
        names = {'first': 'John'}
        data = {'ssn': '1234567890', 'names': names}
        serializer = PersonIdentifierSerializer(data=data)

        expected_names = {'first': 'John', 'last': '', 'initials': ''}
        data['names'] = expected_names

        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, data)
        self.assertFalse(serializer.object is expected_names)
        self.assertEqual(serializer.data['names'], expected_names)

    def test_null_nested(self):
        """Test a serializer with a nonexistent nested field"""
        data = {'ssn': '1234567890'}
        serializer = PersonIdentifierSerializer(data=data)

        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, data)
        self.assertFalse(serializer.object is data)
        expected = {'ssn': '1234567890', 'names': None}
        self.assertEqual(serializer.data, expected)

    def test_update(self):
        serializer = CommentSerializer(self.comment, data=self.data)
        expected = self.comment
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, expected)
        self.assertTrue(serializer.object is expected)
        self.assertEqual(serializer.data['sub_comment'], 'And Merry Christmas!')

    def test_partial_update(self):
        msg = 'Merry New Year!'
        partial_data = {'content': msg}
        serializer = CommentSerializer(self.comment, data=partial_data)
        self.assertEqual(serializer.is_valid(), False)
        serializer = CommentSerializer(self.comment, data=partial_data, partial=True)
        expected = self.comment
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, expected)
        self.assertTrue(serializer.object is expected)
        self.assertEqual(serializer.data['content'], msg)

    def test_model_fields_as_expected(self):
        """
        Make sure that the fields returned are the same as defined
        in the Meta data
        """
        serializer = PersonSerializer(self.person)
        self.assertEqual(set(serializer.data.keys()),
                          set(['name', 'age', 'info']))

    def test_field_with_dictionary(self):
        """
        Make sure that dictionaries from fields are left intact
        """
        serializer = PersonSerializer(self.person)
        expected = self.person_data
        self.assertEqual(serializer.data['info'], expected)

    def test_read_only_fields(self):
        """
        Attempting to update fields set as read_only should have no effect.
        """
        serializer = PersonSerializer(self.person, data={'name': 'dwight', 'age': 99})
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(serializer.errors, {})
        # Assert age is unchanged (35)
        self.assertEqual(instance.age, self.person_data['age'])

    def test_invalid_read_only_fields(self):
        """
        Regression test for #652.
        """
        self.assertRaises(AssertionError, PersonSerializerInvalidReadOnly, [])

    def test_serializer_data_is_cleared_on_save(self):
        """
        Check _data attribute is cleared on `save()`

        Regression test for #1116
            — id field is not populated if `data` is accessed prior to `save()`
        """
        serializer = ActionItemSerializer(self.actionitem)
        self.assertIsNone(serializer.data.get('id',None), 'New instance. `id` should not be set.')
        serializer.save()
        self.assertIsNotNone(serializer.data.get('id',None), 'Model is saved. `id` should be set.')

    def test_fields_marked_as_not_required_are_excluded_from_validation(self):
        """
        Check that fields with `required=False` are included in list of exclusions.
        """
        serializer = ActionItemSerializerOptionalFields(self.actionitem)
        exclusions = serializer.get_validation_exclusions()
        self.assertTrue('title' in exclusions, '`title` field was marked `required=False` and should be excluded')


class DictStyleSerializer(serializers.Serializer):
    """
    Note that we don't have any `restore_object` method, so the default
    case of simply returning a dict will apply.
    """
    email = serializers.EmailField()


class DictStyleSerializerTests(TestCase):
    def test_dict_style_deserialize(self):
        """
        Ensure serializers can deserialize into a dict.
        """
        data = {'email': 'foo@example.com'}
        serializer = DictStyleSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, data)

    def test_dict_style_serialize(self):
        """
        Ensure serializers can serialize dict objects.
        """
        data = {'email': 'foo@example.com'}
        serializer = DictStyleSerializer(data)
        self.assertEqual(serializer.data, data)


class ValidationTests(TestCase):
    def setUp(self):
        self.comment = Comment(
            'tom@example.com',
            'Happy new year!',
            datetime.datetime(2012, 1, 1)
        )
        self.data = {
            'email': 'tom@example.com',
            'content': 'x' * 1001,
            'created': datetime.datetime(2012, 1, 1)
        }
        self.actionitem = ActionItem(title='Some to do item',)

    def test_create(self):
        serializer = CommentSerializer(data=self.data)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, {'content': ['Ensure this value has at most 1000 characters (it has 1001).']})

    def test_update(self):
        serializer = CommentSerializer(self.comment, data=self.data)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, {'content': ['Ensure this value has at most 1000 characters (it has 1001).']})

    def test_update_missing_field(self):
        data = {
            'content': 'xxx',
            'created': datetime.datetime(2012, 1, 1)
        }
        serializer = CommentSerializer(self.comment, data=data)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, {'email': ['This field is required.']})

    def test_missing_bool_with_default(self):
        """Make sure that a boolean value with a 'False' value is not
        mistaken for not having a default."""
        data = {
            'title': 'Some action item',
            #No 'done' value.
        }
        serializer = ActionItemSerializer(self.actionitem, data=data)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.errors, {})

    def test_cross_field_validation(self):

        class CommentSerializerWithCrossFieldValidator(CommentSerializer):

            def validate(self, attrs):
                if attrs["email"] not in attrs["content"]:
                    raise serializers.ValidationError("Email address not in content")
                return attrs

        data = {
            'email': 'tom@example.com',
            'content': 'A comment from tom@example.com',
            'created': datetime.datetime(2012, 1, 1)
        }

        serializer = CommentSerializerWithCrossFieldValidator(data=data)
        self.assertTrue(serializer.is_valid())

        data['content'] = 'A comment from foo@bar.com'

        serializer = CommentSerializerWithCrossFieldValidator(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'non_field_errors': ['Email address not in content']})

    def test_null_is_true_fields(self):
        """
        Omitting a value for null-field should validate.
        """
        serializer = PersonSerializer(data={'name': 'marko'})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.errors, {})

    def test_modelserializer_max_length_exceeded(self):
        data = {
            'title': 'x' * 201,
        }
        serializer = ActionItemSerializer(data=data)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, {'title': ['Ensure this value has at most 200 characters (it has 201).']})

    def test_modelserializer_max_length_exceeded_with_custom_restore(self):
        """
        When overriding ModelSerializer.restore_object, validation tests should still apply.
        Regression test for #623.

        https://github.com/tomchristie/django-rest-framework/pull/623
        """
        data = {
            'title': 'x' * 201,
        }
        serializer = ActionItemSerializerCustomRestore(data=data)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, {'title': ['Ensure this value has at most 200 characters (it has 201).']})

    def test_default_modelfield_max_length_exceeded(self):
        data = {
            'title': 'Testing "info" field...',
            'info': 'x' * 13,
        }
        serializer = ActionItemSerializer(data=data)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, {'info': ['Ensure this value has at most 12 characters (it has 13).']})

    def test_datetime_validation_failure(self):
        """
        Test DateTimeField validation errors on non-str values.
        Regression test for #669.

        https://github.com/tomchristie/django-rest-framework/issues/669
        """
        data = self.data
        data['created'] = 0

        serializer = CommentSerializer(data=data)
        self.assertEqual(serializer.is_valid(), False)

        self.assertIn('created', serializer.errors)

    def test_missing_model_field_exception_msg(self):
        """
        Assert that a meaningful exception message is outputted when the model
        field is missing (e.g. when mistyping ``model``).
        """
        class BrokenModelSerializer(serializers.ModelSerializer):
            class Meta:
                fields = ['some_field']

        try:
            BrokenModelSerializer()
        except AssertionError as e:
            self.assertEqual(e.args[0], "Serializer class 'BrokenModelSerializer' is missing 'model' Meta option")
        except:
            self.fail('Wrong exception type thrown.')

    def test_writable_star_source_on_nested_serializer(self):
        """
        Assert that a nested serializer instantiated with source='*' correctly
        expands the data into the outer serializer.
        """
        serializer = ModelSerializerWithNestedSerializer(data={
            'name': 'marko',
            'nested': {'info': 'hi'}},
        )
        self.assertEqual(serializer.is_valid(), True)

    def test_writable_star_source_on_nested_serializer_with_parent_object(self):
        class TitleSerializer(serializers.Serializer):
            title = serializers.WritableField(source='title')

        class AlbumSerializer(serializers.ModelSerializer):
            nested = TitleSerializer(source='*')

            class Meta:
                model = Album
                fields = ('nested',)

        class PhotoSerializer(serializers.ModelSerializer):
            album = AlbumSerializer(source='album')

            class Meta:
                model = Photo
                fields = ('album', )

        photo = Photo(album=Album())

        data = {'album': {'nested': {'title': 'test'}}}

        serializer = PhotoSerializer(photo, data=data)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.data, data)

    def test_writable_star_source_with_inner_source_fields(self):
        """
        Tests that a serializer with source="*" correctly expands the
        it's fields into the outer serializer even if they have their
        own 'source' parameters.
        """

        serializer = ModelSerializerWithNestedSerializerWithRenamedField(data={
            'name': 'marko',
            'nested': {'renamed_info': 'hi'}},
        )
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.errors, {})


class CustomValidationTests(TestCase):
    class CommentSerializerWithFieldValidator(CommentSerializer):

        def validate_email(self, attrs, source):
            attrs[source]
            return attrs

        def validate_content(self, attrs, source):
            value = attrs[source]
            if "test" not in value:
                raise serializers.ValidationError("Test not in value")
            return attrs

    def test_field_validation(self):
        data = {
            'email': 'tom@example.com',
            'content': 'A test comment',
            'created': datetime.datetime(2012, 1, 1)
        }

        serializer = self.CommentSerializerWithFieldValidator(data=data)
        self.assertTrue(serializer.is_valid())

        data['content'] = 'This should not validate'

        serializer = self.CommentSerializerWithFieldValidator(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'content': ['Test not in value']})

    def test_missing_data(self):
        """
        Make sure that validate_content isn't called if the field is missing
        """
        incomplete_data = {
            'email': 'tom@example.com',
            'created': datetime.datetime(2012, 1, 1)
        }
        serializer = self.CommentSerializerWithFieldValidator(data=incomplete_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'content': ['This field is required.']})

    def test_wrong_data(self):
        """
        Make sure that validate_content isn't called if the field input is wrong
        """
        wrong_data = {
            'email': 'not an email',
            'content': 'A test comment',
            'created': datetime.datetime(2012, 1, 1)
        }
        serializer = self.CommentSerializerWithFieldValidator(data=wrong_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'email': ['Enter a valid email address.']})

    def test_partial_update(self):
        """
        Make sure that validate_email isn't called when partial=True and email
        isn't found in data.
        """
        initial_data = {
            'email': 'tom@example.com',
            'content': 'A test comment',
            'created': datetime.datetime(2012, 1, 1)
        }

        serializer = self.CommentSerializerWithFieldValidator(data=initial_data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.object

        new_content = 'An *updated* test comment'
        partial_data = {
            'content': new_content
        }

        serializer = self.CommentSerializerWithFieldValidator(instance=instance,
                                                              data=partial_data,
                                                              partial=True)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.object
        self.assertEqual(instance.content, new_content)


class PositiveIntegerAsChoiceTests(TestCase):
    def test_positive_integer_in_json_is_correctly_parsed(self):
        data = {'some_integer': 1}
        serializer = PositiveIntegerAsChoiceSerializer(data=data)
        self.assertEqual(serializer.is_valid(), True)


class ModelValidationTests(TestCase):
    def test_validate_unique(self):
        """
        Just check if serializers.ModelSerializer handles unique checks via .full_clean()
        """
        serializer = AlbumsSerializer(data={'title': 'a', 'ref': '1'})
        serializer.is_valid()
        serializer.save()
        second_serializer = AlbumsSerializer(data={'title': 'a'})
        self.assertFalse(second_serializer.is_valid())
        self.assertEqual(second_serializer.errors,  {'title': ['Album with this Title already exists.'],})
        third_serializer = AlbumsSerializer(data=[{'title': 'b', 'ref': '1'}, {'title': 'c'}], many=True)
        self.assertFalse(third_serializer.is_valid())
        self.assertEqual(third_serializer.errors,  [{'ref': ['Album with this Ref already exists.']}, {}])

    def test_foreign_key_is_null_with_partial(self):
        """
        Test ModelSerializer validation with partial=True

        Specifically test that a null foreign key does not pass validation
        """
        album = Album(title='test')
        album.save()

        class PhotoSerializer(serializers.ModelSerializer):
            class Meta:
                model = Photo

        photo_serializer = PhotoSerializer(data={'description': 'test', 'album': album.pk})
        self.assertTrue(photo_serializer.is_valid())
        photo = photo_serializer.save()

        # Updating only the album (foreign key)
        photo_serializer = PhotoSerializer(instance=photo, data={'album': ''}, partial=True)
        self.assertFalse(photo_serializer.is_valid())
        self.assertTrue('album' in photo_serializer.errors)
        self.assertEqual(photo_serializer.errors['album'], photo_serializer.error_messages['required'])

    def test_foreign_key_with_partial(self):
        """
        Test ModelSerializer validation with partial=True

        Specifically test foreign key validation.
        """

        album = Album(title='test')
        album.save()

        class PhotoSerializer(serializers.ModelSerializer):
            class Meta:
                model = Photo

        photo_serializer = PhotoSerializer(data={'description': 'test', 'album': album.pk})
        self.assertTrue(photo_serializer.is_valid())
        photo = photo_serializer.save()

        # Updating only the album (foreign key)
        photo_serializer = PhotoSerializer(instance=photo, data={'album': album.pk}, partial=True)
        self.assertTrue(photo_serializer.is_valid())
        self.assertTrue(photo_serializer.save())

        # Updating only the description
        photo_serializer = PhotoSerializer(instance=photo,
                                           data={'description': 'new'},
                                           partial=True)

        self.assertTrue(photo_serializer.is_valid())
        self.assertTrue(photo_serializer.save())


class RegexValidationTest(TestCase):
    def test_create_failed(self):
        serializer = BookSerializer(data={'isbn': '1234567890'})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'isbn': ['isbn has to be exact 13 numbers']})

        serializer = BookSerializer(data={'isbn': '12345678901234'})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'isbn': ['isbn has to be exact 13 numbers']})

        serializer = BookSerializer(data={'isbn': 'abcdefghijklm'})
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors, {'isbn': ['isbn has to be exact 13 numbers']})

    def test_create_success(self):
        serializer = BookSerializer(data={'isbn': '1234567890123'})
        self.assertTrue(serializer.is_valid())


class MetadataTests(TestCase):
    def test_empty(self):
        serializer = CommentSerializer()
        expected = {
            'email': serializers.CharField,
            'content': serializers.CharField,
            'created': serializers.DateTimeField
        }
        for field_name, field in expected.items():
            self.assertTrue(isinstance(serializer.data.fields[field_name], field))


class ManyToManyTests(TestCase):
    def setUp(self):
        class ManyToManySerializer(serializers.ModelSerializer):
            class Meta:
                model = ManyToManyModel

        self.serializer_class = ManyToManySerializer

        # An anchor instance to use for the relationship
        self.anchor = Anchor()
        self.anchor.save()

        # A model instance with a many to many relationship to the anchor
        self.instance = ManyToManyModel()
        self.instance.save()
        self.instance.rel.add(self.anchor)

        # A serialized representation of the model instance
        self.data = {'id': 1, 'rel': [self.anchor.id]}

    def test_retrieve(self):
        """
        Serialize an instance of a model with a ManyToMany relationship.
        """
        serializer = self.serializer_class(instance=self.instance)
        expected = self.data
        self.assertEqual(serializer.data, expected)

    def test_create(self):
        """
        Create an instance of a model with a ManyToMany relationship.
        """
        data = {'rel': [self.anchor.id]}
        serializer = self.serializer_class(data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(ManyToManyModel.objects.all()), 2)
        self.assertEqual(instance.pk, 2)
        self.assertEqual(list(instance.rel.all()), [self.anchor])

    def test_update(self):
        """
        Update an instance of a model with a ManyToMany relationship.
        """
        new_anchor = Anchor()
        new_anchor.save()
        data = {'rel': [self.anchor.id, new_anchor.id]}
        serializer = self.serializer_class(self.instance, data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(ManyToManyModel.objects.all()), 1)
        self.assertEqual(instance.pk, 1)
        self.assertEqual(list(instance.rel.all()), [self.anchor, new_anchor])

    def test_create_empty_relationship(self):
        """
        Create an instance of a model with a ManyToMany relationship,
        containing no items.
        """
        data = {'rel': []}
        serializer = self.serializer_class(data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(ManyToManyModel.objects.all()), 2)
        self.assertEqual(instance.pk, 2)
        self.assertEqual(list(instance.rel.all()), [])

    def test_update_empty_relationship(self):
        """
        Update an instance of a model with a ManyToMany relationship,
        containing no items.
        """
        new_anchor = Anchor()
        new_anchor.save()
        data = {'rel': []}
        serializer = self.serializer_class(self.instance, data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(ManyToManyModel.objects.all()), 1)
        self.assertEqual(instance.pk, 1)
        self.assertEqual(list(instance.rel.all()), [])

    def test_create_empty_relationship_flat_data(self):
        """
        Create an instance of a model with a ManyToMany relationship,
        containing no items, using a representation that does not support
        lists (eg form data).
        """
        data = MultiValueDict()
        data.setlist('rel', [''])
        serializer = self.serializer_class(data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(ManyToManyModel.objects.all()), 2)
        self.assertEqual(instance.pk, 2)
        self.assertEqual(list(instance.rel.all()), [])


class ReadOnlyManyToManyTests(TestCase):
    def setUp(self):
        class ReadOnlyManyToManySerializer(serializers.ModelSerializer):
            rel = serializers.RelatedField(many=True, read_only=True)

            class Meta:
                model = ReadOnlyManyToManyModel

        self.serializer_class = ReadOnlyManyToManySerializer

        # An anchor instance to use for the relationship
        self.anchor = Anchor()
        self.anchor.save()

        # A model instance with a many to many relationship to the anchor
        self.instance = ReadOnlyManyToManyModel()
        self.instance.save()
        self.instance.rel.add(self.anchor)

        # A serialized representation of the model instance
        self.data = {'rel': [self.anchor.id], 'id': 1, 'text': 'anchor'}

    def test_update(self):
        """
        Attempt to update an instance of a model with a ManyToMany
        relationship.  Not updated due to read_only=True
        """
        new_anchor = Anchor()
        new_anchor.save()
        data = {'rel': [self.anchor.id, new_anchor.id]}
        serializer = self.serializer_class(self.instance, data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(ReadOnlyManyToManyModel.objects.all()), 1)
        self.assertEqual(instance.pk, 1)
        # rel is still as original (1 entry)
        self.assertEqual(list(instance.rel.all()), [self.anchor])

    def test_update_without_relationship(self):
        """
        Attempt to update an instance of a model where many to ManyToMany
        relationship is not supplied.  Not updated due to read_only=True
        """
        new_anchor = Anchor()
        new_anchor.save()
        data = {}
        serializer = self.serializer_class(self.instance, data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(ReadOnlyManyToManyModel.objects.all()), 1)
        self.assertEqual(instance.pk, 1)
        # rel is still as original (1 entry)
        self.assertEqual(list(instance.rel.all()), [self.anchor])


class DefaultValueTests(TestCase):
    def setUp(self):
        class DefaultValueSerializer(serializers.ModelSerializer):
            class Meta:
                model = DefaultValueModel

        self.serializer_class = DefaultValueSerializer
        self.objects = DefaultValueModel.objects

    def test_create_using_default(self):
        data = {}
        serializer = self.serializer_class(data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(self.objects.all()), 1)
        self.assertEqual(instance.pk, 1)
        self.assertEqual(instance.text, 'foobar')

    def test_create_overriding_default(self):
        data = {'text': 'overridden'}
        serializer = self.serializer_class(data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(self.objects.all()), 1)
        self.assertEqual(instance.pk, 1)
        self.assertEqual(instance.text, 'overridden')

    def test_partial_update_default(self):
        """ Regression test for issue #532 """
        data = {'text': 'overridden'}
        serializer = self.serializer_class(data=data, partial=True)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()

        data = {'extra': 'extra_value'}
        serializer = self.serializer_class(instance=instance, data=data, partial=True)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()

        self.assertEqual(instance.extra, 'extra_value')
        self.assertEqual(instance.text, 'overridden')


class WritableFieldDefaultValueTests(TestCase):

    def setUp(self):
        self.expected = {'default': 'value'}
        self.create_field = fields.WritableField

    def test_get_default_value_with_noncallable(self):
        field = self.create_field(default=self.expected)
        got = field.get_default_value()
        self.assertEqual(got, self.expected)

    def test_get_default_value_with_callable(self):
        field = self.create_field(default=lambda : self.expected)
        got = field.get_default_value()
        self.assertEqual(got, self.expected)

    def test_get_default_value_when_not_required(self):
        field = self.create_field(default=self.expected, required=False)
        got = field.get_default_value()
        self.assertEqual(got, self.expected)

    def test_get_default_value_returns_None(self):
        field = self.create_field()
        got = field.get_default_value()
        self.assertIsNone(got)

    def test_get_default_value_returns_non_True_values(self):
        values = [None, '', False, 0, [], (), {}] # values that assumed as 'False' in the 'if' clause
        for expected in values:
            field = self.create_field(default=expected)
            got = field.get_default_value()
            self.assertEqual(got, expected)


class RelatedFieldDefaultValueTests(WritableFieldDefaultValueTests):

    def setUp(self):
        self.expected = {'foo': 'bar'}
        self.create_field = relations.RelatedField

    def test_get_default_value_returns_empty_list(self):
        field = self.create_field(many=True)
        got = field.get_default_value()
        self.assertListEqual(got, [])

    def test_get_default_value_returns_expected(self):
        expected = [1, 2, 3]
        field = self.create_field(many=True, default=expected)
        got = field.get_default_value()
        self.assertListEqual(got, expected)


class CallableDefaultValueTests(TestCase):
    def setUp(self):
        class CallableDefaultValueSerializer(serializers.ModelSerializer):
            class Meta:
                model = CallableDefaultValueModel

        self.serializer_class = CallableDefaultValueSerializer
        self.objects = CallableDefaultValueModel.objects

    def test_create_using_default(self):
        data = {}
        serializer = self.serializer_class(data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(self.objects.all()), 1)
        self.assertEqual(instance.pk, 1)
        self.assertEqual(instance.text, 'foobar')

    def test_create_overriding_default(self):
        data = {'text': 'overridden'}
        serializer = self.serializer_class(data=data)
        self.assertEqual(serializer.is_valid(), True)
        instance = serializer.save()
        self.assertEqual(len(self.objects.all()), 1)
        self.assertEqual(instance.pk, 1)
        self.assertEqual(instance.text, 'overridden')


class ManyRelatedTests(TestCase):
    def test_reverse_relations(self):
        post = BlogPost.objects.create(title="Test blog post")
        post.blogpostcomment_set.create(text="I hate this blog post")
        post.blogpostcomment_set.create(text="I love this blog post")

        class BlogPostCommentSerializer(serializers.Serializer):
            text = serializers.CharField()

        class BlogPostSerializer(serializers.Serializer):
            title = serializers.CharField()
            comments = BlogPostCommentSerializer(source='blogpostcomment_set')

        serializer = BlogPostSerializer(instance=post)
        expected = {
            'title': 'Test blog post',
            'comments': [
                {'text': 'I hate this blog post'},
                {'text': 'I love this blog post'}
            ]
        }

        self.assertEqual(serializer.data, expected)

    def test_include_reverse_relations(self):
        post = BlogPost.objects.create(title="Test blog post")
        post.blogpostcomment_set.create(text="I hate this blog post")
        post.blogpostcomment_set.create(text="I love this blog post")

        class BlogPostSerializer(serializers.ModelSerializer):
            class Meta:
                model = BlogPost
                fields = ('id', 'title', 'blogpostcomment_set')

        serializer = BlogPostSerializer(instance=post)
        expected = {
            'id': 1, 'title': 'Test blog post', 'blogpostcomment_set': [1, 2]
        }
        self.assertEqual(serializer.data, expected)

    def test_depth_include_reverse_relations(self):
        post = BlogPost.objects.create(title="Test blog post")
        post.blogpostcomment_set.create(text="I hate this blog post")
        post.blogpostcomment_set.create(text="I love this blog post")

        class BlogPostSerializer(serializers.ModelSerializer):
            class Meta:
                model = BlogPost
                fields = ('id', 'title', 'blogpostcomment_set')
                depth = 1

        serializer = BlogPostSerializer(instance=post)
        expected = {
            'id': 1, 'title': 'Test blog post',
            'blogpostcomment_set': [
                {'id': 1, 'text': 'I hate this blog post', 'blog_post': 1},
                {'id': 2, 'text': 'I love this blog post', 'blog_post': 1}
            ]
        }
        self.assertEqual(serializer.data, expected)

    def test_callable_source(self):
        post = BlogPost.objects.create(title="Test blog post")
        post.blogpostcomment_set.create(text="I love this blog post")

        class BlogPostCommentSerializer(serializers.Serializer):
            text = serializers.CharField()

        class BlogPostSerializer(serializers.Serializer):
            title = serializers.CharField()
            first_comment = BlogPostCommentSerializer(source='get_first_comment')

        serializer = BlogPostSerializer(post)

        expected = {
            'title': 'Test blog post',
            'first_comment': {'text': 'I love this blog post'}
        }
        self.assertEqual(serializer.data, expected)


class RelatedTraversalTest(TestCase):
    def test_nested_traversal(self):
        """
        Source argument should support dotted.source notation.
        """
        user = Person.objects.create(name="django")
        post = BlogPost.objects.create(title="Test blog post", writer=user)
        post.blogpostcomment_set.create(text="I love this blog post")

        class PersonSerializer(serializers.ModelSerializer):
            class Meta:
                model = Person
                fields = ("name", "age")

        class BlogPostCommentSerializer(serializers.ModelSerializer):
            class Meta:
                model = BlogPostComment
                fields = ("text", "post_owner")

            text = serializers.CharField()
            post_owner = PersonSerializer(source='blog_post.writer')

        class BlogPostSerializer(serializers.Serializer):
            title = serializers.CharField()
            comments = BlogPostCommentSerializer(source='blogpostcomment_set')

        serializer = BlogPostSerializer(instance=post)

        expected = {
            'title': 'Test blog post',
            'comments': [{
                'text': 'I love this blog post',
                'post_owner': {
                    "name": "django",
                    "age": None
                }
            }]
        }

        self.assertEqual(serializer.data, expected)

    def test_nested_traversal_with_none(self):
        """
        If a component of the dotted.source is None, return None for the field.
        """
        from tests.models import NullableForeignKeySource
        instance = NullableForeignKeySource.objects.create(name='Source with null FK')

        class NullableSourceSerializer(serializers.Serializer):
            target_name = serializers.Field(source='target.name')

        serializer = NullableSourceSerializer(instance=instance)

        expected = {
            'target_name': None,
        }

        self.assertEqual(serializer.data, expected)


class SerializerMethodFieldTests(TestCase):
    def setUp(self):

        class BoopSerializer(serializers.Serializer):
            beep = serializers.SerializerMethodField('get_beep')
            boop = serializers.Field()
            boop_count = serializers.SerializerMethodField('get_boop_count')

            def get_beep(self, obj):
                return 'hello!'

            def get_boop_count(self, obj):
                return len(obj.boop)

        self.serializer_class = BoopSerializer

    def test_serializer_method_field(self):

        class MyModel(object):
            boop = ['a', 'b', 'c']

        source_data = MyModel()

        serializer = self.serializer_class(source_data)

        expected = {
            'beep': 'hello!',
            'boop': ['a', 'b', 'c'],
            'boop_count': 3,
        }

        self.assertEqual(serializer.data, expected)


# Test for issue #324
class BlankFieldTests(TestCase):
    def setUp(self):

        class BlankFieldModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = BlankFieldModel

        class BlankFieldSerializer(serializers.Serializer):
            title = serializers.CharField(required=False)

        class NotBlankFieldModelSerializer(serializers.ModelSerializer):
            class Meta:
                model = BasicModel

        class NotBlankFieldSerializer(serializers.Serializer):
            title = serializers.CharField()

        self.model_serializer_class = BlankFieldModelSerializer
        self.serializer_class = BlankFieldSerializer
        self.not_blank_model_serializer_class = NotBlankFieldModelSerializer
        self.not_blank_serializer_class = NotBlankFieldSerializer
        self.data = {'title': ''}

    def test_create_blank_field(self):
        serializer = self.serializer_class(data=self.data)
        self.assertEqual(serializer.is_valid(), True)

    def test_create_model_blank_field(self):
        serializer = self.model_serializer_class(data=self.data)
        self.assertEqual(serializer.is_valid(), True)

    def test_create_model_null_field(self):
        serializer = self.model_serializer_class(data={'title': None})
        self.assertEqual(serializer.is_valid(), True)

    def test_create_not_blank_field(self):
        """
        Test to ensure blank data in a field not marked as blank=True
        is considered invalid in a non-model serializer
        """
        serializer = self.not_blank_serializer_class(data=self.data)
        self.assertEqual(serializer.is_valid(), False)

    def test_create_model_not_blank_field(self):
        """
        Test to ensure blank data in a field not marked as blank=True
        is considered invalid in a model serializer
        """
        serializer = self.not_blank_model_serializer_class(data=self.data)
        self.assertEqual(serializer.is_valid(), False)

    def test_create_model_empty_field(self):
        serializer = self.model_serializer_class(data={})
        self.assertEqual(serializer.is_valid(), True)

    def test_create_model_null_field_save(self):
        """
        Regression test for #1330.

        https://github.com/tomchristie/django-rest-framework/pull/1330
        """
        serializer = self.model_serializer_class(data={'title': None})
        self.assertEqual(serializer.is_valid(), True)

        try:
            serializer.save()
        except Exception:
            self.fail('Exception raised on save() after validation passes')


#test for issue #460
class SerializerPickleTests(TestCase):
    """
    Test pickleability of the output of Serializers
    """
    def test_pickle_simple_model_serializer_data(self):
        """
        Test simple serializer
        """
        pickle.dumps(PersonSerializer(Person(name="Methusela", age=969)).data)

    def test_pickle_inner_serializer(self):
        """
        Test pickling a serializer whose resulting .data (a SortedDictWithMetadata) will
        have unpickleable meta data--in order to make sure metadata doesn't get pulled into the pickle.
        See DictWithMetadata.__getstate__
        """
        class InnerPersonSerializer(serializers.ModelSerializer):
            class Meta:
                model = Person
                fields = ('name', 'age')
        pickle.dumps(InnerPersonSerializer(Person(name="Noah", age=950)).data, 0)

    def test_getstate_method_should_not_return_none(self):
        """
        Regression test for #645.
        """
        data = serializers.DictWithMetadata({1: 1})
        self.assertEqual(data.__getstate__(), serializers.SortedDict({1: 1}))

    def test_serializer_data_is_pickleable(self):
        """
        Another regression test for #645.
        """
        data = serializers.SortedDictWithMetadata({1: 1})
        repr(pickle.loads(pickle.dumps(data, 0)))


# test for issue #725
class SeveralChoicesModel(models.Model):
    color = models.CharField(
        max_length=10,
        choices=[('red', 'Red'), ('green', 'Green'), ('blue', 'Blue')],
        blank=False
    )
    drink = models.CharField(
        max_length=10,
        choices=[('beer', 'Beer'), ('wine', 'Wine'), ('cider', 'Cider')],
        blank=False,
        default='beer'
    )
    os = models.CharField(
        max_length=10,
        choices=[('linux', 'Linux'), ('osx', 'OSX'), ('windows', 'Windows')],
        blank=True
    )
    music_genre = models.CharField(
        max_length=10,
        choices=[('rock', 'Rock'), ('metal', 'Metal'), ('grunge', 'Grunge')],
        blank=True,
        default='metal'
    )


class SerializerChoiceFields(TestCase):

    def setUp(self):
        super(SerializerChoiceFields, self).setUp()

        class SeveralChoicesSerializer(serializers.ModelSerializer):
            class Meta:
                model = SeveralChoicesModel
                fields = ('color', 'drink', 'os', 'music_genre')

        self.several_choices_serializer = SeveralChoicesSerializer

    def test_choices_blank_false_not_default(self):
        serializer = self.several_choices_serializer()
        self.assertEqual(
            serializer.fields['color'].choices,
            [('red', 'Red'), ('green', 'Green'), ('blue', 'Blue')]
        )

    def test_choices_blank_false_with_default(self):
        serializer = self.several_choices_serializer()
        self.assertEqual(
            serializer.fields['drink'].choices,
            [('beer', 'Beer'), ('wine', 'Wine'), ('cider', 'Cider')]
        )

    def test_choices_blank_true_not_default(self):
        serializer = self.several_choices_serializer()
        self.assertEqual(
            serializer.fields['os'].choices,
            BLANK_CHOICE_DASH + [('linux', 'Linux'), ('osx', 'OSX'), ('windows', 'Windows')]
        )

    def test_choices_blank_true_with_default(self):
        serializer = self.several_choices_serializer()
        self.assertEqual(
            serializer.fields['music_genre'].choices,
            BLANK_CHOICE_DASH + [('rock', 'Rock'), ('metal', 'Metal'), ('grunge', 'Grunge')]
        )


# Regression tests for #675
class Ticket(models.Model):
    assigned = models.ForeignKey(
        Person, related_name='assigned_tickets')
    reviewer = models.ForeignKey(
        Person, blank=True, null=True, related_name='reviewed_tickets')


class SerializerRelatedChoicesTest(TestCase):

    def setUp(self):
        super(SerializerRelatedChoicesTest, self).setUp()

        class RelatedChoicesSerializer(serializers.ModelSerializer):
            class Meta:
                model = Ticket
                fields = ('assigned', 'reviewer')

        self.related_fields_serializer = RelatedChoicesSerializer

    def test_empty_queryset_required(self):
        serializer = self.related_fields_serializer()
        self.assertEqual(serializer.fields['assigned'].queryset.count(), 0)
        self.assertEqual(
            [x for x in serializer.fields['assigned'].widget.choices],
            []
        )

    def test_empty_queryset_not_required(self):
        serializer = self.related_fields_serializer()
        self.assertEqual(serializer.fields['reviewer'].queryset.count(), 0)
        self.assertEqual(
            [x for x in serializer.fields['reviewer'].widget.choices],
            [('', '---------')]
        )

    def test_with_some_persons_required(self):
        Person.objects.create(name="Lionel Messi")
        Person.objects.create(name="Xavi Hernandez")
        serializer = self.related_fields_serializer()
        self.assertEqual(serializer.fields['assigned'].queryset.count(), 2)
        self.assertEqual(
            [x for x in serializer.fields['assigned'].widget.choices],
            [(1, 'Person object - 1'), (2, 'Person object - 2')]
        )

    def test_with_some_persons_not_required(self):
        Person.objects.create(name="Lionel Messi")
        Person.objects.create(name="Xavi Hernandez")
        serializer = self.related_fields_serializer()
        self.assertEqual(serializer.fields['reviewer'].queryset.count(), 2)
        self.assertEqual(
            [x for x in serializer.fields['reviewer'].widget.choices],
            [('', '---------'), (1, 'Person object - 1'), (2, 'Person object - 2')]
        )


class DepthTest(TestCase):
    def test_implicit_nesting(self):

        writer = Person.objects.create(name="django", age=1)
        post = BlogPost.objects.create(title="Test blog post", writer=writer)
        comment = BlogPostComment.objects.create(text="Test blog post comment", blog_post=post)

        class BlogPostCommentSerializer(serializers.ModelSerializer):
            class Meta:
                model = BlogPostComment
                depth = 2

        serializer = BlogPostCommentSerializer(instance=comment)
        expected = {'id': 1, 'text': 'Test blog post comment', 'blog_post': {'id': 1, 'title': 'Test blog post',
                    'writer': {'id': 1, 'name': 'django', 'age': 1}}}

        self.assertEqual(serializer.data, expected)

    def test_explicit_nesting(self):
        writer = Person.objects.create(name="django", age=1)
        post = BlogPost.objects.create(title="Test blog post", writer=writer)
        comment = BlogPostComment.objects.create(text="Test blog post comment", blog_post=post)

        class PersonSerializer(serializers.ModelSerializer):
            class Meta:
                model = Person

        class BlogPostSerializer(serializers.ModelSerializer):
            writer = PersonSerializer()

            class Meta:
                model = BlogPost

        class BlogPostCommentSerializer(serializers.ModelSerializer):
            blog_post = BlogPostSerializer()

            class Meta:
                model = BlogPostComment

        serializer = BlogPostCommentSerializer(instance=comment)
        expected = {'id': 1, 'text': 'Test blog post comment', 'blog_post': {'id': 1, 'title': 'Test blog post',
                    'writer': {'id': 1, 'name': 'django', 'age': 1}}}

        self.assertEqual(serializer.data, expected)


class NestedSerializerContextTests(TestCase):

    def test_nested_serializer_context(self):
        """
        Regression for #497

        https://github.com/tomchristie/django-rest-framework/issues/497
        """
        class PhotoSerializer(serializers.ModelSerializer):
            class Meta:
                model = Photo
                fields = ("description", "callable")

            callable = serializers.SerializerMethodField('_callable')

            def _callable(self, instance):
                if not 'context_item' in self.context:
                    raise RuntimeError("context isn't getting passed into 2nd level nested serializer")
                return "success"

        class AlbumSerializer(serializers.ModelSerializer):
            class Meta:
                model = Album
                fields = ("photo_set", "callable")

            photo_set = PhotoSerializer(source="photo_set", many=True)
            callable = serializers.SerializerMethodField("_callable")

            def _callable(self, instance):
                if not 'context_item' in self.context:
                    raise RuntimeError("context isn't getting passed into 1st level nested serializer")
                return "success"

        class AlbumCollection(object):
            albums = None

        class AlbumCollectionSerializer(serializers.Serializer):
            albums = AlbumSerializer(source="albums", many=True)

        album1 = Album.objects.create(title="album 1")
        album2 = Album.objects.create(title="album 2")
        Photo.objects.create(description="Bigfoot", album=album1)
        Photo.objects.create(description="Unicorn", album=album1)
        Photo.objects.create(description="Yeti", album=album2)
        Photo.objects.create(description="Sasquatch", album=album2)
        album_collection = AlbumCollection()
        album_collection.albums = [album1, album2]

        # This will raise RuntimeError if context doesn't get passed correctly to the nested Serializers
        AlbumCollectionSerializer(album_collection, context={'context_item': 'album context'}).data


class DeserializeListTestCase(TestCase):

    def setUp(self):
        self.data = {
            'email': 'nobody@nowhere.com',
            'content': 'This is some test content',
            'created': datetime.datetime(2013, 3, 7),
        }

    def test_no_errors(self):
        data = [self.data.copy() for x in range(0, 3)]
        serializer = CommentSerializer(data=data, many=True)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(isinstance(serializer.object, list))
        self.assertTrue(
            all((isinstance(item, Comment) for item in serializer.object))
        )

    def test_errors_return_as_list(self):
        invalid_item = self.data.copy()
        invalid_item['email'] = ''
        data = [self.data.copy(), invalid_item, self.data.copy()]

        serializer = CommentSerializer(data=data, many=True)
        self.assertFalse(serializer.is_valid())
        expected = [{}, {'email': ['This field is required.']}, {}]
        self.assertEqual(serializer.errors, expected)


# Test for issue 747

class LazyStringModel(object):
    def __init__(self, lazystring):
        self.lazystring = lazystring


class LazyStringSerializer(serializers.Serializer):
    lazystring = serializers.Field()

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.lazystring = attrs.get('lazystring', instance.lazystring)
            return instance
        return LazyStringModel(**attrs)


class LazyStringsTestCase(TestCase):
    def setUp(self):
        self.model = LazyStringModel(lazystring=_('lazystring'))

    def test_lazy_strings_are_translated(self):
        serializer = LazyStringSerializer(self.model)
        self.assertEqual(type(serializer.data['lazystring']),
                         type('lazystring'))


# Test for issue #467

class FieldLabelTest(TestCase):
    def setUp(self):
        self.serializer_class = BasicModelSerializer

    def test_label_from_model(self):
        """
        Validates that label and help_text are correctly copied from the model class.
        """
        serializer = self.serializer_class()
        text_field = serializer.fields['text']

        self.assertEqual('Text comes here', text_field.label)
        self.assertEqual('Text description.', text_field.help_text)

    def test_field_ctor(self):
        """
        This is check that ctor supports both label and help_text.
        """
        self.assertEqual('Label', fields.Field(label='Label', help_text='Help').label)
        self.assertEqual('Help', fields.CharField(label='Label', help_text='Help').help_text)
        self.assertEqual('Label', relations.HyperlinkedRelatedField(view_name='fake', label='Label', help_text='Help', many=True).label)


# Test for issue #961

class ManyFieldHelpTextTest(TestCase):
    def test_help_text_no_hold_down_control_msg(self):
        """
        Validate that help_text doesn't contain the 'Hold down "Control" ...'
        message that Django appends to choice fields.
        """
        rel_field = fields.Field(help_text=ManyToManyModel._meta.get_field('rel').help_text)
        self.assertEqual('Some help text.', rel_field.help_text)


class AttributeMappingOnAutogeneratedRelatedFields(TestCase):

    def test_primary_key_related_field(self):
        serializer = ForeignKeySourceSerializer()
        self.assertEqual(serializer.fields['target'].help_text, 'Target')
        self.assertEqual(serializer.fields['target'].label, 'Target')

    def test_hyperlinked_related_field(self):
        serializer = HyperlinkedForeignKeySourceSerializer()
        self.assertEqual(serializer.fields['target'].help_text, 'Target')
        self.assertEqual(serializer.fields['target'].label, 'Target')


@unittest.skipUnless(PIL is not None, 'PIL is not installed')
class AttributeMappingOnAutogeneratedFieldsTests(TestCase):

    def setUp(self):

        class AMOAFSerializer(serializers.ModelSerializer):
            class Meta:
                model = AMOAFModel

        self.serializer_class = AMOAFSerializer
        self.fields_attributes = {
            'char_field': [
                ('max_length', 1024),
            ],
            'comma_separated_integer_field': [
                ('max_length', 1024),
            ],
            'decimal_field': [
                ('max_digits', 64),
                ('decimal_places', 32),
            ],
            'email_field': [
                ('max_length', 1024),
            ],
            'file_field': [
                ('max_length', 1024),
            ],
            'image_field': [
                ('max_length', 1024),
            ],
            'slug_field': [
                ('max_length', 1024),
            ],
            'url_field': [
                ('max_length', 1024),
            ],
            'nullable_char_field': [
                ('max_length', 1024),
                ('allow_none', True),
            ],
        }

    def field_test(self, field):
        serializer = self.serializer_class(data={})
        self.assertEqual(serializer.is_valid(), True)

        for attribute in self.fields_attributes[field]:
            self.assertEqual(
                getattr(serializer.fields[field], attribute[0]),
                attribute[1]
            )

    def test_char_field(self):
        self.field_test('char_field')

    def test_comma_separated_integer_field(self):
        self.field_test('comma_separated_integer_field')

    def test_decimal_field(self):
        self.field_test('decimal_field')

    def test_email_field(self):
        self.field_test('email_field')

    def test_file_field(self):
        self.field_test('file_field')

    def test_image_field(self):
        self.field_test('image_field')

    def test_slug_field(self):
        self.field_test('slug_field')

    def test_url_field(self):
        self.field_test('url_field')

    def test_nullable_char_field(self):
        self.field_test('nullable_char_field')


@unittest.skipUnless(PIL is not None, 'PIL is not installed')
class DefaultValuesOnAutogeneratedFieldsTests(TestCase):

    def setUp(self):

        class DVOAFSerializer(serializers.ModelSerializer):
            class Meta:
                model = DVOAFModel

        self.serializer_class = DVOAFSerializer
        self.fields_attributes = {
            'positive_integer_field': [
                ('min_value', 0),
            ],
            'positive_small_integer_field': [
                ('min_value', 0),
            ],
            'email_field': [
                ('max_length', 75),
            ],
            'file_field': [
                ('max_length', 100),
            ],
            'image_field': [
                ('max_length', 100),
            ],
            'slug_field': [
                ('max_length', 50),
            ],
            'url_field': [
                ('max_length', 200),
            ],
        }

    def field_test(self, field):
        serializer = self.serializer_class(data={})
        self.assertEqual(serializer.is_valid(), True)

        for attribute in self.fields_attributes[field]:
            self.assertEqual(
                getattr(serializer.fields[field], attribute[0]),
                attribute[1]
            )

    def test_positive_integer_field(self):
        self.field_test('positive_integer_field')

    def test_positive_small_integer_field(self):
        self.field_test('positive_small_integer_field')

    def test_email_field(self):
        self.field_test('email_field')

    def test_file_field(self):
        self.field_test('file_field')

    def test_image_field(self):
        self.field_test('image_field')

    def test_slug_field(self):
        self.field_test('slug_field')

    def test_url_field(self):
        self.field_test('url_field')


class MetadataSerializer(serializers.Serializer):
    field1 = serializers.CharField(3, required=True)
    field2 = serializers.CharField(10, required=False)


class MetadataSerializerTestCase(TestCase):
    def setUp(self):
        self.serializer = MetadataSerializer()

    def test_serializer_metadata(self):
        metadata = self.serializer.metadata()
        expected = {
            'field1': {
                'required': True,
                'max_length': 3,
                'type': 'string',
                'read_only': False
            },
            'field2': {
                'required': False,
                'max_length': 10,
                'type': 'string',
                'read_only': False
            }
        }
        self.assertEqual(expected, metadata)


### Regression test for #840

class SimpleModel(models.Model):
    text = models.CharField(max_length=100)


class SimpleModelSerializer(serializers.ModelSerializer):
    text = serializers.CharField()
    other = serializers.CharField()

    class Meta:
        model = SimpleModel

    def validate_other(self, attrs, source):
        del attrs['other']
        return attrs


class FieldValidationRemovingAttr(TestCase):
    def test_removing_non_model_field_in_validation(self):
        """
        Removing an attr during field valiation should ensure that it is not
        passed through when restoring the object.

        This allows additional non-model fields to be supported.

        Regression test for #840.
        """
        serializer = SimpleModelSerializer(data={'text': 'foo', 'other': 'bar'})
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.object.text, 'foo')


### Regression test for #878

class SimpleTargetModel(models.Model):
    text = models.CharField(max_length=100)


class SimplePKSourceModelSerializer(serializers.Serializer):
    targets = serializers.PrimaryKeyRelatedField(queryset=SimpleTargetModel.objects.all(), many=True)
    text = serializers.CharField()


class SimpleSlugSourceModelSerializer(serializers.Serializer):
    targets = serializers.SlugRelatedField(queryset=SimpleTargetModel.objects.all(), many=True, slug_field='pk')
    text = serializers.CharField()


class SerializerSupportsManyRelationships(TestCase):
    def setUp(self):
        SimpleTargetModel.objects.create(text='foo')
        SimpleTargetModel.objects.create(text='bar')

    def test_serializer_supports_pk_many_relationships(self):
        """
        Regression test for #878.

        Note that pk behavior has a different code path to usual cases,
        for performance reasons.
        """
        serializer = SimplePKSourceModelSerializer(data={'text': 'foo', 'targets': [1, 2]})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, {'text': 'foo', 'targets': [1, 2]})

    def test_serializer_supports_slug_many_relationships(self):
        """
        Regression test for #878.
        """
        serializer = SimpleSlugSourceModelSerializer(data={'text': 'foo', 'targets': [1, 2]})
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data, {'text': 'foo', 'targets': [1, 2]})


class TransformMethodsSerializer(serializers.Serializer):
    a = serializers.CharField()
    b_renamed = serializers.CharField(source='b')

    def transform_a(self, obj, value):
        return value.lower()

    def transform_b_renamed(self, obj, value):
        if value is not None:
            return 'and ' + value


class TestSerializerTransformMethods(TestCase):
    def setUp(self):
        self.s = TransformMethodsSerializer()

    def test_transform_methods(self):
        self.assertEqual(
            self.s.to_native({'a': 'GREEN EGGS', 'b': 'HAM'}),
            {
                'a': 'green eggs',
                'b_renamed': 'and HAM',
            }
        )

    def test_missing_fields(self):
        self.assertEqual(
            self.s.to_native({'a': 'GREEN EGGS'}),
            {
                'a': 'green eggs',
                'b_renamed': None,
            }
        )


class DefaultTrueBooleanModel(models.Model):
    cat = models.BooleanField(default=True)
    dog = models.BooleanField(default=False)


class SerializerDefaultTrueBoolean(TestCase):

    def setUp(self):
        super(SerializerDefaultTrueBoolean, self).setUp()

        class DefaultTrueBooleanSerializer(serializers.ModelSerializer):
            class Meta:
                model = DefaultTrueBooleanModel
                fields = ('cat', 'dog')

        self.default_true_boolean_serializer = DefaultTrueBooleanSerializer

    def test_enabled_as_false(self):
        serializer = self.default_true_boolean_serializer(data={'cat': False,
                                                                'dog': False})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.data['cat'], False)
        self.assertEqual(serializer.data['dog'], False)

    def test_enabled_as_true(self):
        serializer = self.default_true_boolean_serializer(data={'cat': True,
                                                                'dog': True})
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.data['cat'], True)
        self.assertEqual(serializer.data['dog'], True)

    def test_enabled_partial(self):
        serializer = self.default_true_boolean_serializer(data={'cat': False},
                                                          partial=True)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.data['cat'], False)
        self.assertEqual(serializer.data['dog'], False)


class BoolenFieldTypeTest(TestCase):
    '''
    Ensure the various Boolean based model fields are rendered as the proper
    field type

    '''

    def setUp(self):
        '''
        Setup an ActionItemSerializer for BooleanTesting
        '''
        data = {
            'title': 'b' * 201,
        }
        self.serializer = ActionItemSerializer(data=data)

    def test_booleanfield_type(self):
        '''
        Test that BooleanField is infered from models.BooleanField
        '''
        bfield = self.serializer.get_fields()['done']
        self.assertEqual(type(bfield), fields.BooleanField)

    def test_nullbooleanfield_type(self):
        '''
        Test that BooleanField is infered from models.NullBooleanField

        https://groups.google.com/forum/#!topic/django-rest-framework/D9mXEftpuQ8
        '''
        bfield = self.serializer.get_fields()['started']
        self.assertEqual(type(bfield), fields.BooleanField)
