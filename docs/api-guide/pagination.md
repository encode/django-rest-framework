<a class="github" href="pagination.py"></a>

# Pagination

> Django provides a few classes that help you manage paginated data – that is, data that’s split across several pages, with “Previous/Next” links.
>
> &mdash; [Django documentation][cite]

REST framework includes a `PaginationSerializer` class that makes it easy to return paginated data in a way that can then be rendered to arbitrary media types. 

## Examples

Let's start by taking a look at an example from the Django documentation.

    from django.core.paginator import Paginator
    objects = ['john', 'paul', 'george', 'ringo']
    paginator = Paginator(objects, 2)
    page = paginator.page(1)
    page.object_list
    # ['john', 'paul']

At this point we've got a page object.  If we wanted to return this page object as a JSON response, we'd need to provide the client with context such as next and previous links, so that it would be able to page through the remaining results.

    from rest_framework.pagination import PaginationSerializer
    serializer = PaginationSerializer(instance=page)
    serializer.data
    # {'count': 4, 'next': '?page=2', 'previous': None, 'results': [u'john', u'paul']}

The `context` argument of the `PaginationSerializer` class may optionally include the request.  If the request is included in the context then the next and previous links returned by the serializer will use absolute URLs instead of relative URLs.

    request = RequestFactory().get('/foobar')
    serializer = PaginationSerializer(instance=page, context={'request': request})
    serializer.data
    # {'count': 4, 'next': 'http://testserver/foobar?page=2', 'previous': None, 'results': [u'john', u'paul']}    

We could now return that data in a `Response` object, and it would be rendered into the correct media type.

Our first example worked because we were using primative objects.  If we wanted to paginate a queryset or other complex data, we'd need to specify a serializer to use to serialize the result set itself with.

We can do this using the `object_serializer_class` attribute on the inner `Meta` class of the pagination serializer.  For example.

    class UserSerializer(serializers.ModelSerializer):
        """
        Serializes user querysets.
        """
        class Meta:
            model = User
            fields = ('username', 'email')

    class PaginatedUserSerializer(pagination.PaginationSerializer):
        """
        Serializes page objects of user querysets.
        """
        class Meta:
            object_serializer_class = UserSerializer

    queryset = User.objects.all()
    paginator = Paginator(queryset, 20)
    page = paginator.page(1)
    serializer = PaginatedUserSerializer(instance=page)
    serializer.data
    # {'count': 1, 'next': None, 'previous': None, 'results': [{'username': u'admin', 'email': u'admin@example.com'}]}

## Pagination in the generic views

The generic class based views `ListAPIView` and `ListCreateAPIView` provide pagination of the returned querysets by default.  You can customise this behaviour by altering the pagination style, by modifying the default number of results, or by turning pagination off completely.

## Setting the default pagination style

The default pagination style may be set globally, using the `PAGINATION_SERIALIZER` and `PAGINATE_BY` settings.  For example.

    REST_FRAMEWORK = {
        'PAGINATION_SERIALIZER': (
            'example_app.pagination.CustomPaginationSerializer',
        ),
        'PAGINATE_BY': 10
    }

You can also set the pagination style on a per-view basis, using the `ListAPIView` generic class-based view.

    class PaginatedListView(ListAPIView):
        model = ExampleModel
        pagination_serializer_class = CustomPaginationSerializer
        paginate_by = 10

## Creating custom pagination serializers

Override `pagination.BasePaginationSerializer`, and set the fields that you want the serializer to return.

For example.

    class CustomPaginationSerializer(pagination.BasePaginationSerializer):
        next = pagination.NextURLField()
        total_results = serializers.Field(source='paginator.count')


[cite]: https://docs.djangoproject.com/en/dev/topics/pagination/

