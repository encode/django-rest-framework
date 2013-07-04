from __future__ import unicode_literals
import json
from django.test import TestCase
from rest_framework import generics, status, serializers
from rest_framework.compat import patterns, url
from rest_framework.test import APIRequestFactory
from rest_framework.tests.models import (
    Anchor, BasicModel, ManyToManyModel, BlogPost, BlogPostComment,
    Album, Photo, OptionalRelationModel
)

factory = APIRequestFactory()


class BlogPostCommentSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='blogpostcomment-detail')
    text = serializers.CharField()
    blog_post_url = serializers.HyperlinkedRelatedField(source='blog_post', view_name='blogpost-detail')

    class Meta:
        model = BlogPostComment
        fields = ('text', 'blog_post_url', 'url')


class PhotoSerializer(serializers.Serializer):
    description = serializers.CharField()
    album_url = serializers.HyperlinkedRelatedField(source='album', view_name='album-detail', queryset=Album.objects.all(), lookup_field='title', slug_url_kwarg='title')

    def restore_object(self, attrs, instance=None):
        return Photo(**attrs)


class AlbumSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='album-detail', lookup_field='title')

    class Meta:
        model = Album
        fields = ('title', 'url')


class BasicList(generics.ListCreateAPIView):
    model = BasicModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


class BasicDetail(generics.RetrieveUpdateDestroyAPIView):
    model = BasicModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


class AnchorDetail(generics.RetrieveAPIView):
    model = Anchor
    model_serializer_class = serializers.HyperlinkedModelSerializer


class ManyToManyList(generics.ListAPIView):
    model = ManyToManyModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


class ManyToManyDetail(generics.RetrieveAPIView):
    model = ManyToManyModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


class BlogPostCommentListCreate(generics.ListCreateAPIView):
    model = BlogPostComment
    serializer_class = BlogPostCommentSerializer


class BlogPostCommentDetail(generics.RetrieveAPIView):
    model = BlogPostComment
    serializer_class = BlogPostCommentSerializer


class BlogPostDetail(generics.RetrieveAPIView):
    model = BlogPost


class PhotoListCreate(generics.ListCreateAPIView):
    model = Photo
    model_serializer_class = PhotoSerializer


class AlbumDetail(generics.RetrieveAPIView):
    model = Album
    serializer_class = AlbumSerializer
    lookup_field = 'title'


class OptionalRelationDetail(generics.RetrieveUpdateDestroyAPIView):
    model = OptionalRelationModel
    model_serializer_class = serializers.HyperlinkedModelSerializer


urlpatterns = patterns('',
    url(r'^basic/$', BasicList.as_view(), name='basicmodel-list'),
    url(r'^basic/(?P<pk>\d+)/$', BasicDetail.as_view(), name='basicmodel-detail'),
    url(r'^anchor/(?P<pk>\d+)/$', AnchorDetail.as_view(), name='anchor-detail'),
    url(r'^manytomany/$', ManyToManyList.as_view(), name='manytomanymodel-list'),
    url(r'^manytomany/(?P<pk>\d+)/$', ManyToManyDetail.as_view(), name='manytomanymodel-detail'),
    url(r'^posts/(?P<pk>\d+)/$', BlogPostDetail.as_view(), name='blogpost-detail'),
    url(r'^comments/$', BlogPostCommentListCreate.as_view(), name='blogpostcomment-list'),
    url(r'^comments/(?P<pk>\d+)/$', BlogPostCommentDetail.as_view(), name='blogpostcomment-detail'),
    url(r'^albums/(?P<title>\w[\w-]*)/$', AlbumDetail.as_view(), name='album-detail'),
    url(r'^photos/$', PhotoListCreate.as_view(), name='photo-list'),
    url(r'^optionalrelation/(?P<pk>\d+)/$', OptionalRelationDetail.as_view(), name='optionalrelationmodel-detail'),
)


class TestBasicHyperlinkedView(TestCase):
    urls = 'rest_framework.tests.test_hyperlinkedserializers'

    def setUp(self):
        """
        Create 3 BasicModel instances.
        """
        items = ['foo', 'bar', 'baz']
        for item in items:
            BasicModel(text=item).save()
        self.objects = BasicModel.objects
        self.data = [
            {'url': 'http://testserver/basic/%d/' % obj.id, 'text': obj.text}
            for obj in self.objects.all()
        ]
        self.list_view = BasicList.as_view()
        self.detail_view = BasicDetail.as_view()

    def test_get_list_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/basic/')
        response = self.list_view(request).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

    def test_get_detail_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/basic/1')
        response = self.detail_view(request, pk=1).render()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data[0])


class TestManyToManyHyperlinkedView(TestCase):
    urls = 'rest_framework.tests.test_hyperlinkedserializers'

    def setUp(self):
        """
        Create 3 BasicModel instances.
        """
        items = ['foo', 'bar', 'baz']
        anchors = []
        for item in items:
            anchor = Anchor(text=item)
            anchor.save()
            anchors.append(anchor)

        manytomany = ManyToManyModel()
        manytomany.save()
        manytomany.rel.add(*anchors)

        self.data = [{
            'url': 'http://testserver/manytomany/1/',
            'rel': [
                'http://testserver/anchor/1/',
                'http://testserver/anchor/2/',
                'http://testserver/anchor/3/',
            ]
        }]
        self.list_view = ManyToManyList.as_view()
        self.detail_view = ManyToManyDetail.as_view()

    def test_get_list_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/manytomany/')
        response = self.list_view(request)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

    def test_get_detail_view(self):
        """
        GET requests to ListCreateAPIView should return list of objects.
        """
        request = factory.get('/manytomany/1/')
        response = self.detail_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data[0])


class TestHyperlinkedIdentityFieldLookup(TestCase):
    urls = 'rest_framework.tests.test_hyperlinkedserializers'

    def setUp(self):
        """
        Create 3 Album instances.
        """
        titles = ['foo', 'bar', 'baz']
        for title in titles:
            album = Album(title=title)
            album.save()
        self.detail_view = AlbumDetail.as_view()
        self.data = {
            'foo': {'title': 'foo', 'url': 'http://testserver/albums/foo/'},
            'bar': {'title': 'bar', 'url': 'http://testserver/albums/bar/'},
            'baz': {'title': 'baz', 'url': 'http://testserver/albums/baz/'}
        }

    def test_lookup_field(self):
        """
        GET requests to AlbumDetail view should return serialized Albums
        with a url field keyed by `title`.
        """
        for album in Album.objects.all():
            request = factory.get('/albums/{0}/'.format(album.title))
            response = self.detail_view(request, title=album.title)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data, self.data[album.title])


class TestCreateWithForeignKeys(TestCase):
    urls = 'rest_framework.tests.test_hyperlinkedserializers'

    def setUp(self):
        """
        Create a blog post
        """
        self.post = BlogPost.objects.create(title="Test post")
        self.create_view = BlogPostCommentListCreate.as_view()

    def test_create_comment(self):

        data = {
            'text': 'A test comment',
            'blog_post_url': 'http://testserver/posts/1/'
        }

        request = factory.post('/comments/', data=data)
        response = self.create_view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response['Location'], 'http://testserver/comments/1/')
        self.assertEqual(self.post.blogpostcomment_set.count(), 1)
        self.assertEqual(self.post.blogpostcomment_set.all()[0].text, 'A test comment')


class TestCreateWithForeignKeysAndCustomSlug(TestCase):
    urls = 'rest_framework.tests.test_hyperlinkedserializers'

    def setUp(self):
        """
        Create an Album
        """
        self.post = Album.objects.create(title='test-album')
        self.list_create_view = PhotoListCreate.as_view()

    def test_create_photo(self):

        data = {
            'description': 'A test photo',
            'album_url': 'http://testserver/albums/test-album/'
        }

        request = factory.post('/photos/', data=data)
        response = self.list_create_view(request)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('Location', response, msg='Location should only be included if there is a "url" field on the serializer')
        self.assertEqual(self.post.photo_set.count(), 1)
        self.assertEqual(self.post.photo_set.all()[0].description, 'A test photo')


class TestOptionalRelationHyperlinkedView(TestCase):
    urls = 'rest_framework.tests.test_hyperlinkedserializers'

    def setUp(self):
        """
        Create 1 OptionalRelationModel instances.
        """
        OptionalRelationModel().save()
        self.objects = OptionalRelationModel.objects
        self.detail_view = OptionalRelationDetail.as_view()
        self.data = {"url": "http://testserver/optionalrelation/1/", "other": None}

    def test_get_detail_view(self):
        """
        GET requests to RetrieveAPIView with optional relations should return None
        for non existing relations.
        """
        request = factory.get('/optionalrelationmodel-detail/1')
        response = self.detail_view(request, pk=1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.data)

    def test_put_detail_view(self):
        """
        PUT requests to RetrieveUpdateDestroyAPIView with optional relations
        should accept None for non existing relations.
        """
        response = self.client.put('/optionalrelation/1/',
                                   data=json.dumps(self.data),
                                   content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestOverriddenURLField(TestCase):
    def setUp(self):
        class OverriddenURLSerializer(serializers.HyperlinkedModelSerializer):
            url = serializers.SerializerMethodField('get_url')

            class Meta:
                model = BlogPost
                fields = ('title', 'url')

            def get_url(self, obj):
                return 'foo bar'

        self.Serializer = OverriddenURLSerializer
        self.obj = BlogPost.objects.create(title='New blog post')

    def test_overridden_url_field(self):
        """
        The 'url' field should respect overriding.
        Regression test for #936.
        """
        serializer = self.Serializer(self.obj)
        self.assertEqual(
            serializer.data,
            {'title': 'New blog post', 'url': 'foo bar'}
        )
