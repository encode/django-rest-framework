from __future__ import unicode_literals
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation, GenericForeignKey
from django.db import models
from django.test import TestCase, RequestFactory

from rest_framework import serializers
from rest_framework.compat import patterns, url
from rest_framework.genericrelations import GenericRelationOption, GenericRelatedField
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


class Contact(models.Model):
    """
    A textual note that may have multiple tags attached.
    """
    name = models.TextField()
    slug = models.SlugField()
    tags = GenericRelation(Tag)

    def __unicode__(self):
        return 'Contact: %s' % self.name


class TestGenericRelationOptions(TestCase):

    def test_default_related_field(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail')
        self.assertIsInstance(option.related_field, serializers.HyperlinkedRelatedField)

    def test_default_related_field_view_name(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail')
        self.assertEqual(option.related_field.view_name, 'bookmark-detail')

    def test_default_serializer(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail')
        self.assertIsInstance(option.serializer, serializers.ModelSerializer)

    def test_default_serializer_meta_model(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail')
        self.assertEqual(option.serializer.Meta.model, Bookmark)

    def test_get_url_output_resolver(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail')
        self.assertIsInstance(option.get_output_resolver(), serializers.HyperlinkedRelatedField)

    def test_get_url_output_resolver_with_queryset(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail')
        self.assertIsNotNone(option.get_output_resolver().queryset)

    def test_get_input_resolver(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail')
        self.assertIsInstance(option.get_input_resolver(), serializers.HyperlinkedRelatedField)

    def test_get_input_resolver_with_queryset(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail')
        self.assertIsNotNone(option.get_output_resolver().queryset)

    def test_get_serializer_resolver(self):
        option = GenericRelationOption(Bookmark, 'bookmark-detail', as_hyperlink=False)
        self.assertIsInstance(option.get_output_resolver(), serializers.ModelSerializer)

    def test_custom_related_field(self):
        related_field = serializers.HyperlinkedRelatedField(view_name='bookmark-detail', format='xml')
        option = GenericRelationOption(Bookmark, 'bookmark-detail',
            related_field=related_field)
        self.assertEqual(option.related_field.format, 'xml')

    def test_custom_serializer(self):

        class BookmarkSerializer(serializers.ModelSerializer):
            class Meta:
                model = Bookmark
                exclude = ('id', )

        serializer = BookmarkSerializer()
        option = GenericRelationOption(Bookmark, 'bookmark-detail', as_hyperlink=False, serializer=serializer)
        self.assertIn('id', option.get_output_resolver().Meta.exclude)


class TestGenericRelatedFieldToNative(TestCase):

    urls = 'rest_framework.tests.relations_generic'

    def setUp(self):
        self.bookmark = Bookmark.objects.create(url='https://www.djangoproject.com/')
        Tag.objects.create(tagged_item=self.bookmark, tag='django')
        Tag.objects.create(tagged_item=self.bookmark, tag='python')
        self.note = Note.objects.create(text='Remember the milk')
        Tag.objects.create(tagged_item=self.note, tag='reminder')

    def test_relations_as_hyperlinks(self):

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField([
                GenericRelationOption(Bookmark, 'bookmark-detail'),
                GenericRelationOption(Note, 'note-detail'),
            ], source='tagged_item')

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(Tag.objects.all(), many=True)
        expected = [
            {
                'tagged_item': '/bookmark/1/',
                'tag': u'django'
            },
            {
                'tagged_item': '/bookmark/1/',
                'tag': u'python'
            },
            {
                'tagged_item': '/note/1/',
                'tag': u'reminder'
            }
        ]
        self.assertEqual(serializer.data, expected)

    def test_relations_as_nested(self):

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField([
                GenericRelationOption(Bookmark, 'bookmark-detail'),
                GenericRelationOption(Note, 'note-detail', as_hyperlink=False),
            ], source='tagged_item')

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(Tag.objects.all(), many=True)
        expected = [
            {
                'tagged_item': '/bookmark/1/',
                'tag': u'django'
            },
            {
                'tagged_item': '/bookmark/1/',
                'tag': u'python'
            },
            {
                'tagged_item': {
                    'id': 1,
                    'text': 'Remember the milk',
                },
                'tag': u'reminder'
            }
        ]
        self.assertEqual(serializer.data, expected)

    def test_custom_related_field(self):
        contact = Contact.objects.create(name='Lukas Buenger', slug='lukas-buenger')
        Tag.objects.create(tagged_item=contact, tag='developer')

        contact_related_field = serializers.HyperlinkedRelatedField(view_name='contact-detail',
            slug_url_kwarg='my_own_slug')

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField([
                GenericRelationOption(Bookmark, 'bookmark-detail'),
                GenericRelationOption(Note, 'note-detail', as_hyperlink=False),
                GenericRelationOption(Contact, 'contact-detail', related_field=contact_related_field),
            ], source='tagged_item')

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(Tag.objects.all(), many=True)
        expected = [
            {
                'tagged_item': '/bookmark/1/',
                'tag': u'django'
            },
            {
                'tagged_item': '/bookmark/1/',
                'tag': u'python'
            },
            {
                'tagged_item': {
                    'id': 1,
                    'text': 'Remember the milk',
                },
                'tag': u'reminder'
            },
            {
                'tagged_item': '/contact/lukas-buenger/',
                'tag': u'developer'
            }
        ]
        self.assertEqual(serializer.data, expected)

    def test_custom_serializer(self):
        contact = Contact.objects.create(name='Lukas Buenger', slug='lukas-buenger')
        Tag.objects.create(tagged_item=contact, tag='developer')

        contact_related_field = serializers.HyperlinkedRelatedField(view_name='contact-detail',
                    slug_url_kwarg='my_own_slug')

        class ContactSerializer(serializers.ModelSerializer):
            class Meta:
                model = Contact
                exclude = ('id', 'slug', )


        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField([
                GenericRelationOption(Bookmark, 'bookmark-detail'),
                GenericRelationOption(Note, 'note-detail', as_hyperlink=False),
                GenericRelationOption(Contact, 'contact-detail', as_hyperlink=False, related_field=contact_related_field,
                    serializer=ContactSerializer()),
            ], source='tagged_item')

            class Meta:
                model = Tag
                exclude = ('id', 'content_type', 'object_id', )

        serializer = TagSerializer(Tag.objects.all(), many=True)
        expected = [
            {
                'tagged_item': '/bookmark/1/',
                'tag': u'django'
            },
            {
                'tagged_item': '/bookmark/1/',
                'tag': u'python'
            },
            {
                'tagged_item': {
                    'id': 1,
                    'text': 'Remember the milk',
                },
                'tag': u'reminder'
            },
            {
                'tagged_item': {
                    'name': 'Lukas Buenger'
                 },
                'tag': u'developer'
            }
        ]
        self.assertEqual(serializer.data, expected)


class TestGenericRelatedFieldFromNative(TestCase):

    urls = 'rest_framework.tests.relations_generic'

    def setUp(self):
        self.bookmark = Bookmark.objects.create(url='https://www.djangoproject.com/')
        Tag.objects.create(tagged_item=self.bookmark, tag='django')
        Tag.objects.create(tagged_item=self.bookmark, tag='python')
        self.note = Note.objects.create(text='Remember the milk')

    def test_default(self):

        class TagSerializer(serializers.ModelSerializer):
            tagged_item = GenericRelatedField([
                GenericRelationOption(Bookmark, 'bookmark-detail'),
                GenericRelationOption(Note, 'note-detail'),
            ], source='tagged_item')

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
            'tag': u'reminder'
        }
        self.assertEqual(serializer.data, expected)
