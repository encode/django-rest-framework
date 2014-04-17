from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation, GenericForeignKey
from django.db import models
from django.test import TestCase
from rest_framework import serializers
from rest_framework.compat import python_2_unicode_compatible


@python_2_unicode_compatible
class Tag(models.Model):
    """
    Tags have a descriptive slug, and are attached to an arbitrary object.
    """
    tag = models.SlugField()
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    tagged_item = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return self.tag


@python_2_unicode_compatible
class Bookmark(models.Model):
    """
    A URL bookmark that may have multiple tags attached.
    """
    url = models.URLField()
    tags = GenericRelation(Tag)

    def __str__(self):
        return 'Bookmark: %s' % self.url


@python_2_unicode_compatible
class Note(models.Model):
    """
    A textual note that may have multiple tags attached.
    """
    text = models.TextField()
    tags = GenericRelation(Tag)

    def __str__(self):
        return 'Note: %s' % self.text


class TestGenericRelations(TestCase):
    def setUp(self):
        self.bookmark = Bookmark.objects.create(url='https://www.djangoproject.com/')
        Tag.objects.create(tagged_item=self.bookmark, tag='django')
        Tag.objects.create(tagged_item=self.bookmark, tag='python')
        self.note = Note.objects.create(text='Remember the milk')
        Tag.objects.create(tagged_item=self.note, tag='reminder')

    def test_generic_relation(self):
        """
        Test a relationship that spans a GenericRelation field.
        IE. A reverse generic relationship.
        """

        class BookmarkSerializer(serializers.ModelSerializer):
            tags = serializers.RelatedField(many=True)

            class Meta:
                model = Bookmark
                exclude = ('id',)

        serializer = BookmarkSerializer(self.bookmark)
        expected = {
            'tags': ['django', 'python'],
            'url': 'https://www.djangoproject.com/'
        }
        self.assertEqual(serializer.data, expected)

    def test_generic_nested_relation(self):
        """
        Test saving a GenericRelation field via a nested serializer.
        """

        class TagSerializer(serializers.ModelSerializer):
            class Meta:
                model = Tag
                exclude = ('content_type', 'object_id')

        class BookmarkSerializer(serializers.ModelSerializer):
            tags = TagSerializer()

            class Meta:
                model = Bookmark
                exclude = ('id',)

        data = {
            'url': 'https://docs.djangoproject.com/',
            'tags': [
                {'tag': 'contenttypes'},
                {'tag': 'genericrelations'},
            ]
        }
        serializer = BookmarkSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.assertEqual(serializer.object.tags.count(), 2)

    def test_generic_fk(self):
        """
        Test a relationship that spans a GenericForeignKey field.
        IE. A forward generic relationship.
        """

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = serializers.RelatedField()

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id')

        serializer = TagSerializer(Tag.objects.all(), many=True)
        expected = [
        {
            'tag': 'django',
            'tagged_item': 'Bookmark: https://www.djangoproject.com/'
        },
        {
            'tag': 'python',
            'tagged_item': 'Bookmark: https://www.djangoproject.com/'
        },
        {
            'tag': 'reminder',
            'tagged_item': 'Note: Remember the milk'
        }
        ]
        self.assertEqual(serializer.data, expected)

    def test_restore_object_generic_fk(self):
        """
        Ensure an object with a generic foreign key can be restored.
        """

        class TagSerializer(serializers.ModelSerializer):
            class Meta:
                model = Tag
                exclude = ('content_type', 'object_id')

        serializer = TagSerializer()

        bookmark = Bookmark(url='http://example.com')
        attrs = {'tagged_item': bookmark, 'tag': 'example'}

        tag = serializer.restore_object(attrs)
        self.assertEqual(tag.tagged_item, bookmark)
