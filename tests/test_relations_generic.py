from __future__ import unicode_literals

from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.test import TestCase
from django.utils.encoding import python_2_unicode_compatible

from rest_framework import serializers


@python_2_unicode_compatible
class Tag(models.Model):
    """
    Tags have a descriptive slug, and are attached to an arbitrary object.
    """
    tag = models.SlugField()
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
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
            tags = serializers.StringRelatedField(many=True)

            class Meta:
                model = Bookmark
                fields = ('tags', 'url')

        serializer = BookmarkSerializer(self.bookmark)
        expected = {
            'tags': ['django', 'python'],
            'url': 'https://www.djangoproject.com/'
        }
        assert serializer.data == expected

    def test_generic_fk(self):
        """
        Test a relationship that spans a GenericForeignKey field.
        IE. A forward generic relationship.
        """

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = serializers.StringRelatedField()

            class Meta:
                model = Tag
                fields = ('tag', 'tagged_item')

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
        assert serializer.data == expected
