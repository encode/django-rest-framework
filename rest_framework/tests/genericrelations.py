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
    content_object = GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.tag


class Bookmark(models.Model):
    """
    A URL bookmark that may have multiple tags attached.
    """
    url = models.URLField()
    tags = GenericRelation(Tag)


class TestGenericRelations(TestCase):
    def setUp(self):
        self.bookmark = Bookmark.objects.create(url='https://www.djangoproject.com/')
        Tag.objects.create(content_object=self.bookmark, tag='django')
        Tag.objects.create(content_object=self.bookmark, tag='python')

    def test_reverse_generic_relation(self):
        """
        Test a relationship that spans a GenericRelation field.
        """

        class BookmarkSerializer(serializers.ModelSerializer):
            tags = serializers.ManyRelatedField(source='tags')

            class Meta:
                model = Bookmark
                exclude = ('id',)

        serializer = BookmarkSerializer(self.bookmark)
        expected = {
            'tags': [u'django', u'python'],
            'url': u'https://www.djangoproject.com/'
        }
        self.assertEquals(serializer.data, expected)
