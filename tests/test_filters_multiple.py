import datetime

from django.db import models
from django.test import TestCase

from rest_framework import filters, generics, serializers
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


class Post(models.Model):
    name = models.CharField(max_length=20)


class Author(models.Model):
    name = models.CharField(max_length=20)


class EntryRecord(models.Model):
    blog = models.ForeignKey(Post, on_delete=models.CASCADE)
    authors = models.ManyToManyField(Author, related_name='entries', blank=True)
    headline = models.CharField(max_length=120)
    pub_date = models.DateField(null=True)


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = '__all__'


class EntryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryRecord
        fields = '__all__'


class SearchFilterToManyTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        b1 = Post.objects.create(name='Post 1')
        b2 = Post.objects.create(name='Post 2')

        a1 = Author.objects.create(name='alice')
        a2 = Author.objects.create(name='bob')

        # Multiple entries on Lennon published in 1979 - distinct should deduplicate
        e1 = EntryRecord.objects.create(blog=b1, headline='Something about Lennon', pub_date=datetime.date(1979, 1, 1))
        e1.authors.add(a1)
        e1.save()

        e2 = EntryRecord.objects.create(blog=b1, headline='Another thing about Lennon', pub_date=datetime.date(1979, 6, 1))
        e2.authors.add(a2)
        e2.save()

        # EntryRecord on Lennon *and* a separate entryrecord in 1979 - should not match
        e3 = EntryRecord.objects.create(blog=b2, headline='Something unrelated', pub_date=datetime.date(1979, 1, 1))

        e4 = EntryRecord.objects.create(blog=b2, headline='Retrospective on Lennon', pub_date=datetime.date(1990, 6, 1))
        e4.authors.add(a1)
        e4.authors.add(a2)
        e4.save()

    def setUp(self):
        class SearchPostListView(generics.ListAPIView):
            queryset = Post.objects.all()
            serializer_class = PostSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = (
                '=name',
                'entryrecord__headline',
                '=entryrecord__pub_date__year',
                'entryrecord__authors__name'
            )

        self.SearchPostListView = SearchPostListView

        class SearchEntryRecordListView(generics.ListAPIView):
            queryset = EntryRecord.objects.all()
            serializer_class = EntryRecordSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = (
                'authors__name',
            )

        self.SearchEntryRecordListView = SearchEntryRecordListView

    def test_multiple_filter_conditions(self):
        view = self.SearchPostListView.as_view()
        request = factory.get('/', {'search': 'Lennon, 1979'})
        response = view(request)
        assert len(response.data) == 1

    def test_single_filter_condition_manytomany(self):
        view = self.SearchPostListView.as_view()

        request = factory.get('/', {'search': 'alice'})
        response = view(request)
        assert len(response.data) == 2

        request = factory.get('/', {'search': 'bob'})
        response = view(request)
        assert len(response.data) == 2

    def test_multiple_filter_conditions_manytomany(self):
        view = self.SearchEntryRecordListView.as_view()
        request = factory.get('/', {'search': 'alice, bob'})
        response = view(request)
        assert len(response.data) == 1

        dual_entry = EntryRecord.objects.get(headline='Retrospective on Lennon')
        response_id = response.data[0].get('id')
        assert response_id == dual_entry.id
