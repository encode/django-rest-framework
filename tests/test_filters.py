import datetime
from importlib import reload as reload_module

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.db.models import CharField, Transform
from django.db.models.functions import Concat, Upper
from django.test import TestCase
from django.test.utils import override_settings

from rest_framework import filters, generics, serializers
from rest_framework.compat import coreschema
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


class BaseFilterTests(TestCase):
    def setUp(self):
        self.original_coreapi = filters.coreapi
        filters.coreapi = True  # mock it, because not None value needed
        self.filter_backend = filters.BaseFilterBackend()

    def tearDown(self):
        filters.coreapi = self.original_coreapi

    def test_filter_queryset_raises_error(self):
        with pytest.raises(NotImplementedError):
            self.filter_backend.filter_queryset(None, None, None)

    @pytest.mark.skipif(not coreschema, reason='coreschema is not installed')
    def test_get_schema_fields_checks_for_coreapi(self):
        filters.coreapi = None
        with pytest.raises(AssertionError):
            self.filter_backend.get_schema_fields({})
        filters.coreapi = True
        assert self.filter_backend.get_schema_fields({}) == []


class SearchFilterModel(models.Model):
    title = models.CharField(max_length=20)
    text = models.CharField(max_length=100)


class SearchFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilterModel
        fields = '__all__'


class SearchFilterTests(TestCase):
    def setUp(self):
        # Sequence of title/text is:
        #
        # z   abc
        # zz  bcd
        # zzz cde
        # ...
        for idx in range(10):
            title = 'z' * (idx + 1)
            text = (
                chr(idx + ord('a')) +
                chr(idx + ord('b')) +
                chr(idx + ord('c'))
            )
            SearchFilterModel(title=title, text=text).save()

    def test_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', 'text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'b'})
        response = view(request)
        assert response.data == [
            {'id': 1, 'title': 'z', 'text': 'abc'},
            {'id': 2, 'title': 'zz', 'text': 'bcd'}
        ]

    def test_search_returns_same_queryset_if_no_search_fields_or_terms_provided(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)

        view = SearchListView.as_view()
        request = factory.get('/')
        response = view(request)
        expected = SearchFilterSerializer(SearchFilterModel.objects.all(),
                                          many=True).data
        assert response.data == expected

    def test_exact_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('=title', 'text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'zzz'})
        response = view(request)
        assert response.data == [
            {'id': 3, 'title': 'zzz', 'text': 'cde'}
        ]

    def test_startswith_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title', '^text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'b'})
        response = view(request)
        assert response.data == [
            {'id': 2, 'title': 'zz', 'text': 'bcd'}
        ]

    def test_regexp_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('$title', '$text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'z{2} ^b'})
        response = view(request)
        assert response.data == [
            {'id': 2, 'title': 'zz', 'text': 'bcd'}
        ]

    def test_search_with_nonstandard_search_param(self):
        with override_settings(REST_FRAMEWORK={'SEARCH_PARAM': 'query'}):
            reload_module(filters)

            class SearchListView(generics.ListAPIView):
                queryset = SearchFilterModel.objects.all()
                serializer_class = SearchFilterSerializer
                filter_backends = (filters.SearchFilter,)
                search_fields = ('title', 'text')

            view = SearchListView.as_view()
            request = factory.get('/', {'query': 'b'})
            response = view(request)
            assert response.data == [
                {'id': 1, 'title': 'z', 'text': 'abc'},
                {'id': 2, 'title': 'zz', 'text': 'bcd'}
            ]

        reload_module(filters)

    def test_search_with_filter_subclass(self):
        class CustomSearchFilter(filters.SearchFilter):
            # Filter that dynamically changes search fields
            def get_search_fields(self, view, request):
                if request.query_params.get('title_only'):
                    return ('$title',)
                return super().get_search_fields(view, request)

        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (CustomSearchFilter,)
            search_fields = ('$title', '$text')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': r'^\w{3}$'})
        response = view(request)
        assert len(response.data) == 10

        request = factory.get('/', {'search': r'^\w{3}$', 'title_only': 'true'})
        response = view(request)
        assert response.data == [
            {'id': 3, 'title': 'zzz', 'text': 'cde'}
        ]

    def test_search_field_with_null_characters(self):
        view = generics.GenericAPIView()
        request = factory.get('/?search=\0as%00d\x00f')
        request = view.initialize_request(request)

        terms = filters.SearchFilter().get_search_terms(request)

        assert terms == ['asdf']

    def test_search_field_with_additional_transforms(self):
        from django.test.utils import register_lookup

        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.all()
            serializer_class = SearchFilterSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('text__trim', )

        view = SearchListView.as_view()

        # an example custom transform, that trims `a` from the string.
        class TrimA(Transform):
            function = 'TRIM'
            lookup_name = 'trim'

            def as_sql(self, compiler, connection):
                sql, params = compiler.compile(self.lhs)
                return "trim(%s, 'a')" % sql, params

        with register_lookup(CharField, TrimA):
            # Search including `a`
            request = factory.get('/', {'search': 'abc'})

            response = view(request)
            assert response.data == []

            # Search excluding `a`
            request = factory.get('/', {'search': 'bc'})
            response = view(request)
            assert response.data == [
                {'id': 1, 'title': 'z', 'text': 'abc'},
                {'id': 2, 'title': 'zz', 'text': 'bcd'},
            ]


class AttributeModel(models.Model):
    label = models.CharField(max_length=32)


class SearchFilterModelFk(models.Model):
    title = models.CharField(max_length=20)
    attribute = models.ForeignKey(AttributeModel, on_delete=models.CASCADE)


class SearchFilterFkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilterModelFk
        fields = '__all__'


class SearchFilterFkTests(TestCase):

    def test_must_call_distinct(self):
        filter_ = filters.SearchFilter()
        prefixes = [''] + list(filter_.lookup_prefixes)
        for prefix in prefixes:
            assert not filter_.must_call_distinct(
                SearchFilterModelFk._meta,
                ["%stitle" % prefix]
            )
            assert not filter_.must_call_distinct(
                SearchFilterModelFk._meta,
                ["%stitle" % prefix, "%sattribute__label" % prefix]
            )

    def test_must_call_distinct_restores_meta_for_each_field(self):
        # In this test case the attribute of the fk model comes first in the
        # list of search fields.
        filter_ = filters.SearchFilter()
        prefixes = [''] + list(filter_.lookup_prefixes)
        for prefix in prefixes:
            assert not filter_.must_call_distinct(
                SearchFilterModelFk._meta,
                ["%sattribute__label" % prefix, "%stitle" % prefix]
            )


class SearchFilterModelM2M(models.Model):
    title = models.CharField(max_length=20)
    text = models.CharField(max_length=100)
    attributes = models.ManyToManyField(AttributeModel)


class SearchFilterM2MSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchFilterModelM2M
        fields = '__all__'


class SearchFilterM2MTests(TestCase):
    def setUp(self):
        # Sequence of title/text/attributes is:
        #
        # z   abc [1, 2, 3]
        # zz  bcd [1, 2, 3]
        # zzz cde [1, 2, 3]
        # ...
        for idx in range(3):
            label = 'w' * (idx + 1)
            AttributeModel.objects.create(label=label)

        for idx in range(10):
            title = 'z' * (idx + 1)
            text = (
                chr(idx + ord('a')) +
                chr(idx + ord('b')) +
                chr(idx + ord('c'))
            )
            SearchFilterModelM2M(title=title, text=text).save()
        SearchFilterModelM2M.objects.get(title='zz').attributes.add(1, 2, 3)

    def test_m2m_search(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModelM2M.objects.all()
            serializer_class = SearchFilterM2MSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('=title', 'text', 'attributes__label')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'zz'})
        response = view(request)
        assert len(response.data) == 1

    def test_must_call_distinct(self):
        filter_ = filters.SearchFilter()
        prefixes = [''] + list(filter_.lookup_prefixes)
        for prefix in prefixes:
            assert not filter_.must_call_distinct(
                SearchFilterModelM2M._meta,
                ["%stitle" % prefix]
            )

            assert filter_.must_call_distinct(
                SearchFilterModelM2M._meta,
                ["%stitle" % prefix, "%sattributes__label" % prefix]
            )


class Blog(models.Model):
    name = models.CharField(max_length=20)


class Entry(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    headline = models.CharField(max_length=120)
    pub_date = models.DateField(null=True)


class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blog
        fields = '__all__'


class SearchFilterToManyTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        b1 = Blog.objects.create(name='Blog 1')
        b2 = Blog.objects.create(name='Blog 2')

        # Multiple entries on Lennon published in 1979 - distinct should deduplicate
        Entry.objects.create(blog=b1, headline='Something about Lennon', pub_date=datetime.date(1979, 1, 1))
        Entry.objects.create(blog=b1, headline='Another thing about Lennon', pub_date=datetime.date(1979, 6, 1))

        # Entry on Lennon *and* a separate entry in 1979 - should not match
        Entry.objects.create(blog=b2, headline='Something unrelated', pub_date=datetime.date(1979, 1, 1))
        Entry.objects.create(blog=b2, headline='Retrospective on Lennon', pub_date=datetime.date(1990, 6, 1))

    def test_multiple_filter_conditions(self):
        class SearchListView(generics.ListAPIView):
            queryset = Blog.objects.all()
            serializer_class = BlogSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('=name', 'entry__headline', '=entry__pub_date__year')

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'Lennon,1979'})
        response = view(request)
        assert len(response.data) == 1


class SearchFilterAnnotatedSerializer(serializers.ModelSerializer):
    title_text = serializers.CharField()

    class Meta:
        model = SearchFilterModel
        fields = ('title', 'text', 'title_text')


class SearchFilterAnnotatedFieldTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        SearchFilterModel.objects.create(title='abc', text='def')
        SearchFilterModel.objects.create(title='ghi', text='jkl')

    def test_search_in_annotated_field(self):
        class SearchListView(generics.ListAPIView):
            queryset = SearchFilterModel.objects.annotate(
                title_text=Upper(
                    Concat(models.F('title'), models.F('text'))
                )
            ).all()
            serializer_class = SearchFilterAnnotatedSerializer
            filter_backends = (filters.SearchFilter,)
            search_fields = ('title_text',)

        view = SearchListView.as_view()
        request = factory.get('/', {'search': 'ABCDEF'})
        response = view(request)
        assert len(response.data) == 1
        assert response.data[0]['title_text'] == 'ABCDEF'

    def test_must_call_distinct_subsequent_m2m_fields(self):
        f = filters.SearchFilter()

        queryset = SearchFilterModelM2M.objects.annotate(
            title_text=Upper(
                Concat(models.F('title'), models.F('text'))
            )
        ).all()

        # Sanity check that m2m must call distinct
        assert f.must_call_distinct(queryset, ['attributes'])

        # Annotated field should not prevent m2m must call distinct
        assert f.must_call_distinct(queryset, ['title_text', 'attributes'])


class OrderingFilterModel(models.Model):
    title = models.CharField(max_length=20, verbose_name='verbose title')
    text = models.CharField(max_length=100)


class OrderingFilterRelatedModel(models.Model):
    related_object = models.ForeignKey(OrderingFilterModel, related_name="relateds", on_delete=models.CASCADE)
    index = models.SmallIntegerField(help_text="A non-related field to test with", default=0)


class OrderingFilterSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderingFilterModel
        fields = '__all__'


class OrderingDottedRelatedSerializer(serializers.ModelSerializer):
    related_text = serializers.CharField(source='related_object.text')
    related_title = serializers.CharField(source='related_object.title')

    class Meta:
        model = OrderingFilterRelatedModel
        fields = (
            'related_text',
            'related_title',
            'index',
        )


class DjangoFilterOrderingModel(models.Model):
    date = models.DateField()
    text = models.CharField(max_length=10)

    class Meta:
        ordering = ['-date']


class DjangoFilterOrderingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DjangoFilterOrderingModel
        fields = '__all__'


class OrderingFilterTests(TestCase):
    def setUp(self):
        # Sequence of title/text is:
        #
        # zyx abc
        # yxw bcd
        # xwv cde
        for idx in range(3):
            title = (
                chr(ord('z') - idx) +
                chr(ord('y') - idx) +
                chr(ord('x') - idx)
            )
            text = (
                chr(idx + ord('a')) +
                chr(idx + ord('b')) +
                chr(idx + ord('c'))
            )
            OrderingFilterModel(title=title, text=text).save()

    def test_ordering(self):
        class OrderingListView(generics.ListAPIView):
            queryset = OrderingFilterModel.objects.all()
            serializer_class = OrderingFilterSerializer
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'text'})
        response = view(request)
        assert response.data == [
            {'id': 1, 'title': 'zyx', 'text': 'abc'},
            {'id': 2, 'title': 'yxw', 'text': 'bcd'},
            {'id': 3, 'title': 'xwv', 'text': 'cde'},
        ]

    def test_reverse_ordering(self):
        class OrderingListView(generics.ListAPIView):
            queryset = OrderingFilterModel.objects.all()
            serializer_class = OrderingFilterSerializer
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': '-text'})
        response = view(request)
        assert response.data == [
            {'id': 3, 'title': 'xwv', 'text': 'cde'},
            {'id': 2, 'title': 'yxw', 'text': 'bcd'},
            {'id': 1, 'title': 'zyx', 'text': 'abc'},
        ]

    def test_incorrecturl_extrahyphens_ordering(self):
        class OrderingListView(generics.ListAPIView):
            queryset = OrderingFilterModel.objects.all()
            serializer_class = OrderingFilterSerializer
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': '--text'})
        response = view(request)
        assert response.data == [
            {'id': 3, 'title': 'xwv', 'text': 'cde'},
            {'id': 2, 'title': 'yxw', 'text': 'bcd'},
            {'id': 1, 'title': 'zyx', 'text': 'abc'},
        ]

    def test_incorrectfield_ordering(self):
        class OrderingListView(generics.ListAPIView):
            queryset = OrderingFilterModel.objects.all()
            serializer_class = OrderingFilterSerializer
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'foobar'})
        response = view(request)
        assert response.data == [
            {'id': 3, 'title': 'xwv', 'text': 'cde'},
            {'id': 2, 'title': 'yxw', 'text': 'bcd'},
            {'id': 1, 'title': 'zyx', 'text': 'abc'},
        ]

    def test_default_ordering(self):
        class OrderingListView(generics.ListAPIView):
            queryset = OrderingFilterModel.objects.all()
            serializer_class = OrderingFilterSerializer
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('')
        response = view(request)
        assert response.data == [
            {'id': 3, 'title': 'xwv', 'text': 'cde'},
            {'id': 2, 'title': 'yxw', 'text': 'bcd'},
            {'id': 1, 'title': 'zyx', 'text': 'abc'},
        ]

    def test_default_ordering_using_string(self):
        class OrderingListView(generics.ListAPIView):
            queryset = OrderingFilterModel.objects.all()
            serializer_class = OrderingFilterSerializer
            filter_backends = (filters.OrderingFilter,)
            ordering = 'title'
            ordering_fields = ('text',)

        view = OrderingListView.as_view()
        request = factory.get('')
        response = view(request)
        assert response.data == [
            {'id': 3, 'title': 'xwv', 'text': 'cde'},
            {'id': 2, 'title': 'yxw', 'text': 'bcd'},
            {'id': 1, 'title': 'zyx', 'text': 'abc'},
        ]

    def test_ordering_by_aggregate_field(self):
        # create some related models to aggregate order by
        num_objs = [2, 5, 3]
        for obj, num_relateds in zip(OrderingFilterModel.objects.all(),
                                     num_objs):
            for _ in range(num_relateds):
                new_related = OrderingFilterRelatedModel(
                    related_object=obj
                )
                new_related.save()

        class OrderingListView(generics.ListAPIView):
            serializer_class = OrderingFilterSerializer
            filter_backends = (filters.OrderingFilter,)
            ordering = 'title'
            ordering_fields = '__all__'
            queryset = OrderingFilterModel.objects.all().annotate(
                models.Count("relateds"))

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'relateds__count'})
        response = view(request)
        assert response.data == [
            {'id': 1, 'title': 'zyx', 'text': 'abc'},
            {'id': 3, 'title': 'xwv', 'text': 'cde'},
            {'id': 2, 'title': 'yxw', 'text': 'bcd'},
        ]

    def test_ordering_by_dotted_source(self):

        for index, obj in enumerate(OrderingFilterModel.objects.all()):
            OrderingFilterRelatedModel.objects.create(
                related_object=obj,
                index=index
            )

        class OrderingListView(generics.ListAPIView):
            serializer_class = OrderingDottedRelatedSerializer
            filter_backends = (filters.OrderingFilter,)
            queryset = OrderingFilterRelatedModel.objects.all()

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'related_object__text'})
        response = view(request)
        assert response.data == [
            {'related_title': 'zyx', 'related_text': 'abc', 'index': 0},
            {'related_title': 'yxw', 'related_text': 'bcd', 'index': 1},
            {'related_title': 'xwv', 'related_text': 'cde', 'index': 2},
        ]

        request = factory.get('/', {'ordering': '-index'})
        response = view(request)
        assert response.data == [
            {'related_title': 'xwv', 'related_text': 'cde', 'index': 2},
            {'related_title': 'yxw', 'related_text': 'bcd', 'index': 1},
            {'related_title': 'zyx', 'related_text': 'abc', 'index': 0},
        ]

    def test_ordering_with_nonstandard_ordering_param(self):
        with override_settings(REST_FRAMEWORK={'ORDERING_PARAM': 'order'}):
            reload_module(filters)

            class OrderingListView(generics.ListAPIView):
                queryset = OrderingFilterModel.objects.all()
                serializer_class = OrderingFilterSerializer
                filter_backends = (filters.OrderingFilter,)
                ordering = ('title',)
                ordering_fields = ('text',)

            view = OrderingListView.as_view()
            request = factory.get('/', {'order': 'text'})
            response = view(request)
            assert response.data == [
                {'id': 1, 'title': 'zyx', 'text': 'abc'},
                {'id': 2, 'title': 'yxw', 'text': 'bcd'},
                {'id': 3, 'title': 'xwv', 'text': 'cde'},
            ]

        reload_module(filters)

    def test_get_template_context(self):
        class OrderingListView(generics.ListAPIView):
            ordering_fields = '__all__'
            serializer_class = OrderingFilterSerializer
            queryset = OrderingFilterModel.objects.all()
            filter_backends = (filters.OrderingFilter,)

        request = factory.get('/', {'ordering': 'title'}, HTTP_ACCEPT='text/html')
        view = OrderingListView.as_view()
        response = view(request)

        self.assertContains(response, 'verbose title')

    def test_ordering_with_overridden_get_serializer_class(self):
        class OrderingListView(generics.ListAPIView):
            queryset = OrderingFilterModel.objects.all()
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)

            # note: no ordering_fields and serializer_class specified

            def get_serializer_class(self):
                return OrderingFilterSerializer

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'text'})
        response = view(request)
        assert response.data == [
            {'id': 1, 'title': 'zyx', 'text': 'abc'},
            {'id': 2, 'title': 'yxw', 'text': 'bcd'},
            {'id': 3, 'title': 'xwv', 'text': 'cde'},
        ]

    def test_ordering_with_improper_configuration(self):
        class OrderingListView(generics.ListAPIView):
            queryset = OrderingFilterModel.objects.all()
            filter_backends = (filters.OrderingFilter,)
            ordering = ('title',)
            # note: no ordering_fields and serializer_class
            # or get_serializer_class specified

        view = OrderingListView.as_view()
        request = factory.get('/', {'ordering': 'text'})
        with self.assertRaises(ImproperlyConfigured):
            view(request)


class SensitiveOrderingFilterModel(models.Model):
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=100)


# Three different styles of serializer.
# All should allow ordering by username, but not by password.
class SensitiveDataSerializer1(serializers.ModelSerializer):
    username = serializers.CharField()

    class Meta:
        model = SensitiveOrderingFilterModel
        fields = ('id', 'username')


class SensitiveDataSerializer2(serializers.ModelSerializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    class Meta:
        model = SensitiveOrderingFilterModel
        fields = ('id', 'username', 'password')


class SensitiveDataSerializer3(serializers.ModelSerializer):
    user = serializers.CharField(source='username')

    class Meta:
        model = SensitiveOrderingFilterModel
        fields = ('id', 'user')


class SensitiveOrderingFilterTests(TestCase):
    def setUp(self):
        for idx in range(3):
            username = {0: 'userA', 1: 'userB', 2: 'userC'}[idx]
            password = {0: 'passA', 1: 'passC', 2: 'passB'}[idx]
            SensitiveOrderingFilterModel(username=username, password=password).save()

    def test_order_by_serializer_fields(self):
        for serializer_cls in [
            SensitiveDataSerializer1,
            SensitiveDataSerializer2,
            SensitiveDataSerializer3
        ]:
            class OrderingListView(generics.ListAPIView):
                queryset = SensitiveOrderingFilterModel.objects.all().order_by('username')
                filter_backends = (filters.OrderingFilter,)
                serializer_class = serializer_cls

            view = OrderingListView.as_view()
            request = factory.get('/', {'ordering': '-username'})
            response = view(request)

            if serializer_cls == SensitiveDataSerializer3:
                username_field = 'user'
            else:
                username_field = 'username'

            # Note: Inverse username ordering correctly applied.
            assert response.data == [
                {'id': 3, username_field: 'userC'},
                {'id': 2, username_field: 'userB'},
                {'id': 1, username_field: 'userA'},
            ]

    def test_cannot_order_by_non_serializer_fields(self):
        for serializer_cls in [
            SensitiveDataSerializer1,
            SensitiveDataSerializer2,
            SensitiveDataSerializer3
        ]:
            class OrderingListView(generics.ListAPIView):
                queryset = SensitiveOrderingFilterModel.objects.all().order_by('username')
                filter_backends = (filters.OrderingFilter,)
                serializer_class = serializer_cls

            view = OrderingListView.as_view()
            request = factory.get('/', {'ordering': 'password'})
            response = view(request)

            if serializer_cls == SensitiveDataSerializer3:
                username_field = 'user'
            else:
                username_field = 'username'

            # Note: The passwords are not in order.  Default ordering is used.
            assert response.data == [
                {'id': 1, username_field: 'userA'},  # PassB
                {'id': 2, username_field: 'userB'},  # PassC
                {'id': 3, username_field: 'userC'},  # PassA
            ]
