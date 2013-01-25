from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation, GenericForeignKey
from django.db import models
from django.test import TestCase
from rest_framework import serializers


class Tag(models.Model):
    """
    Tags have a descriptive slug, and are attached to an arbitrary object.
    """
    tag = models.SlugField()
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    tagged_item = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.tag


class Bookmark(models.Model):
    """
    A URL bookmark that may have multiple tags attached.
    """
    url = models.URLField()
    tags = GenericRelation(Tag)

    def __unicode__(self):
        return 'Bookmark: %s' % self.url


class Note(models.Model):
    """
    A textual note that may have multiple tags attached.
    """
    text = models.TextField()
    tags = GenericRelation(Tag)

    def __unicode__(self):
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
            tags = serializers.ManyRelatedField()

            class Meta:
                model = Bookmark
                exclude = ('id',)

        serializer = BookmarkSerializer(self.bookmark)
        expected = {
            'tags': [u'django', u'python'],
            'url': u'https://www.djangoproject.com/'
        }
        self.assertEquals(serializer.data, expected)

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

        serializer = TagSerializer(Tag.objects.all())
        expected = [
        {
            'tag': u'django',
            'tagged_item': u'Bookmark: https://www.djangoproject.com/'
        },
        {
            'tag': u'python',
            'tagged_item': u'Bookmark: https://www.djangoproject.com/'
        },
        {
            'tag': u'reminder',
            'tagged_item': u'Note: Remember the milk'
        }
        ]
        self.assertEquals(serializer.data, expected)
