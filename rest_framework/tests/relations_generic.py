from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation, GenericForeignKey
from django.core.exceptions import ValidationError
from django.db import models
from django.test import TestCase, RequestFactory

from rest_framework import serializers
from rest_framework.compat import patterns, url
from rest_framework.exceptions import ConfigurationError
from rest_framework.genericrelations import GenericRelatedField
from rest_framework.reverse import reverse

factory = RequestFactory()
request = factory.get('/')  # Just to ensure we have a request in the serializer context

def dummy_view(request, pk):
    pass

urlpatterns = patterns('',
    url(r'^bookmark/(?P<pk>[0-9]+)/$', dummy_view, name='bookmark-detail'),
    url(r'^note/(?P<pk>[0-9]+)/$', dummy_view, name='note-detail'),
    url(r'^tag/(?P<pk>[0-9]+)/$', dummy_view, name='tag-detail'),
    url(r'^contact/(?P<my_own_slug>[-\w]+)/$', dummy_view, name='contact-detail'),
)


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


class BookmarkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookmark
        exclude = ('id', )


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        exclude = ('id', )


class TestGenericRelatedFieldDeserialization(TestCase):

    urls = 'rest_framework.tests.relations_generic'

    def setUp(self):
        self.bookmark = Bookmark.objects.create(url='https://www.djangoproject.com/')
        Tag.objects.create(tagged_item=self.bookmark, tag='django')
        Tag.objects.create(tagged_item=self.bookmark, tag='python')
        self.note = Note.objects.create(text='Remember the milk')
        Tag.objects.create(tagged_item=self.note, tag='reminder')

    def test_relations_as_hyperlinks(self):

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                    Bookmark: serializers.HyperlinkedRelatedField(view_name='bookmark-detail'),
                    Note: serializers.HyperlinkedRelatedField(view_name='note-detail'),
                }, source='tagged_item', read_only=True)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(Tag.objects.all(), many=True)
        expected = [
            {
                'tagged_item': '/bookmark/1/',
                'tag': 'django',
            },
            {
                'tagged_item': '/bookmark/1/',
                'tag': 'python',
            },
            {
                'tagged_item': '/note/1/',
                'tag': 'reminder'
            }
        ]
        self.assertEqual(serializer.data, expected)

    def test_relations_as_nested(self):

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                Bookmark: BookmarkSerializer(),
                Note: NoteSerializer(),
            }, source='tagged_item', read_only=True)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(Tag.objects.all(), many=True)
        expected = [
            {
                'tagged_item': {
                    'url': 'https://www.djangoproject.com/'
                },
                'tag': 'django'
            },
            {
                'tagged_item': {
                    'url': 'https://www.djangoproject.com/'
                },
                'tag': 'python'
            },
            {
                'tagged_item': {
                    'text': 'Remember the milk',
                },
                'tag': 'reminder'
            }
        ]
        self.assertEqual(serializer.data, expected)

    def test_mixed_serializers(self):
        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                Bookmark: BookmarkSerializer(),
                Note: serializers.HyperlinkedRelatedField(view_name='note-detail'),
            }, source='tagged_item', read_only=True)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(Tag.objects.all(), many=True)
        expected = [
            {
                'tagged_item': {
                    'url': 'https://www.djangoproject.com/'
                },
                'tag': 'django'
            },
            {
                'tagged_item': {
                    'url': 'https://www.djangoproject.com/'
                },
                'tag': 'python'
            },
            {
                'tagged_item': '/note/1/',
                'tag': 'reminder'
            }
        ]
        self.assertEqual(serializer.data, expected)

    def test_invalid_model(self):
        # Leaving out the Note model should result in a ValidationError
        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                Bookmark: BookmarkSerializer(),
            }, source='tagged_item', read_only=True)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )
        serializer = TagSerializer(Tag.objects.all(), many=True)

        def call_data():
            return serializer.data
        self.assertRaises(ValidationError, call_data)


class TestGenericRelatedFieldSerialization(TestCase):

    urls = 'rest_framework.tests.relations_generic'

    def setUp(self):
        self.bookmark = Bookmark.objects.create(url='https://www.djangoproject.com/')
        Tag.objects.create(tagged_item=self.bookmark, tag='django')
        Tag.objects.create(tagged_item=self.bookmark, tag='python')
        self.note = Note.objects.create(text='Remember the milk')

    def test_hyperlink_serialization(self):
        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                    Bookmark: serializers.HyperlinkedRelatedField(view_name='bookmark-detail'),
                    Note: serializers.HyperlinkedRelatedField(view_name='note-detail'),
                }, source='tagged_item', read_only=False)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(data={
            'tag': 'reminder',
            'tagged_item': reverse('note-detail', kwargs={'pk': self.note.pk})
        })
        serializer.is_valid()
        expected = {
            'tagged_item': '/note/1/',
            'tag': 'reminder'
        }
        self.assertEqual(serializer.data, expected)

    def test_configuration_error(self):
        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                    Bookmark: BookmarkSerializer(),
                    Note: serializers.HyperlinkedRelatedField(view_name='note-detail'),
                }, source='tagged_item', read_only=False)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(data={
            'tag': 'reminder',
            'tagged_item': 'just a string'
        })

        with self.assertRaises(ConfigurationError):
            serializer.fields['tagged_item'].determine_serializer_for_data('just a string')

    def test_not_registered_view_name(self):
        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                    Bookmark: serializers.HyperlinkedRelatedField(view_name='bookmark-detail'),
                }, source='tagged_item', read_only=False)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(data={
            'tag': 'reminder',
            'tagged_item': reverse('note-detail', kwargs={'pk': self.note.pk})
        })
        self.assertFalse(serializer.is_valid())

    def test_invalid_url(self):

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                    Bookmark: serializers.HyperlinkedRelatedField(view_name='bookmark-detail'),
                }, source='tagged_item', read_only=False)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(data={
            'tag': 'reminder',
            'tagged_item': 'foo-bar'
        })

        expected = {
            'tagged_item': ['Could not determine a valid serializer for value %r.' % 'foo-bar']
        }

        self.assertFalse(serializer.is_valid())
        self.assertEqual(expected, serializer.errors)

    def test_serializer_save(self):
        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField({
                    Bookmark: serializers.HyperlinkedRelatedField(view_name='bookmark-detail'),
                    Note: serializers.HyperlinkedRelatedField(view_name='note-detail'),
                }, source='tagged_item', read_only=False)

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(data={
            'tag': 'reminder',
            'tagged_item': reverse('note-detail', kwargs={'pk': self.note.pk})
        })
        serializer.is_valid()
        expected = {
            'tagged_item': '/note/1/',
            'tag': 'reminder'
        }
        serializer.save()
        tag = Tag.objects.get(pk=3)
        self.assertEqual(tag.tagged_item, self.note)