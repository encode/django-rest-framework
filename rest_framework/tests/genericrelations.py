from django.test import TestCase
from rest_framework import serializers, generics
from rest_framework.tests.models import *
from rest_framework.compat import patterns, url


class BookmarkDetail(generics.RetrieveAPIView):
    model = ManyToManyModel
    serializer_class = serializers.HyperlinkedModelSerializer


urlpatterns = patterns('',
    url(r'^bookmark/(?P<pk>\d+)/$', BookmarkDetail.as_view(), name='bookmarks-detail'),
)


class TestGenericRelations(TestCase):

    urls = 'rest_framework.tests.genericrelations'

    def setUp(self):
        bookmark = Bookmark(url='https://www.djangoproject.com/')
        bookmark.save()
        django = Tag(tag_name='django')
        django.save()
        python = Tag(tag_name='python')
        python.save()
        t1 = TaggedItem(content_object=bookmark, tag=django)
        t1.save()
        t2 = TaggedItem(content_object=bookmark, tag=python)
        t2.save()
        self.bookmark = bookmark

    def test_reverse_generic_relation(self):
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

    def test_hyperlinked_generic_relation(self):

        class BookmarkSerializer(serializers.ModelSerializer):
            tags = serializers.ManyHyperlinkedRelatedField(source='tags')

            class Meta:
                model = Bookmark
                exclude = ('id', 'url')

        serializer = BookmarkSerializer(self.bookmark)
        expected = {
            'tags': [u'/bookmark/1/', u'/bookmark/2/']
        }
        self.assertEquals(serializer.data, expected)
