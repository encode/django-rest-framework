<a class="github" href="pagination.py"></a>

# Pagination

> Django provides a few classes that help you manage paginated data – that is, data that’s split across several pages, with “Previous/Next” links.
>
> &mdash; [Django documentation][cite]

REST framework includes a `PaginationSerializer` class that makes it easy to return paginated data in a way that can then be rendered to arbitrary media types. 

## Paginating basic data

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

## Paginating QuerySets

Our first example worked because we were using primitive objects.  If we wanted to paginate a queryset or other complex data, we'd need to specify a serializer to use to serialize the result set itself.

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

We could now use our pagination serializer in a view like this.

    @api_view('GET')
    def user_list(request):
        queryset = User.objects.all()
        paginator = Paginator(queryset, 20)

        page = request.QUERY_PARAMS.get('page')
        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            users = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999),
            # deliver last page of results.
            users = paginator.page(paginator.num_pages)

        serializer_context = {'request': request}
        serializer = PaginatedUserSerializer(users,
                                             context=serializer_context)
        return Response(serializer.data)

## Pagination in the generic views

The generic class based views `ListAPIView` and `ListCreateAPIView` provide pagination of the returned querysets by default.  You can customise this behaviour by altering the pagination style, by modifying the default number of results, by allowing clients to override the page size using a query parameter, or by turning pagination off completely.

The default pagination style may be set globally, using the `DEFAULT_PAGINATION_SERIALIZER_CLASS`, `PAGINATE_BY`, `PAGINATE_BY_PARAM`, and `MAX_PAGINATE_BY` settings.  For example.

    REST_FRAMEWORK = {
        'PAGINATE_BY': 10,                 # Default to 10
        'PAGINATE_BY_PARAM': 'page_size',  # Allow client to override, using `?page_size=xxx`.
        'MAX_PAGINATE_BY': 100             # Maximum limit allowed when using `?page_size=xxx`.
    }

You can also set the pagination style on a per-view basis, using the `ListAPIView` generic class-based view.

    class PaginatedListView(ListAPIView):
        queryset = ExampleModel.objects.all()
        serializer_class = ExampleModelSerializer
        paginate_by = 10
        paginate_by_param = 'page_size'
        max_paginate_by = 100

Note that using a `paginate_by` value of `None` will turn off pagination for the view.

For more complex requirements such as serialization that differs depending on the requested media type you can override the `.get_paginate_by()` and `.get_pagination_serializer_class()` methods.

---

# Custom pagination serializers

To create a custom pagination serializer class you should override `pagination.BasePaginationSerializer` and set the fields that you want the serializer to return.

You can also override the name used for the object list field, by setting the `results_field` attribute, which defaults to `'results'`.

## Example

For example, to nest a pair of links labelled 'prev' and 'next', and set the name for the results field to 'objects', you might use something like this.

    from rest_framework import pagination
    from rest_framework import serializers

    class LinksSerializer(serializers.Serializer):
        next = pagination.NextPageField(source='*')
        prev = pagination.PreviousPageField(source='*')

    class CustomPaginationSerializer(pagination.BasePaginationSerializer):
        links = LinksSerializer(source='*')  # Takes the page object as the source
        total_results = serializers.Field(source='paginator.count')

        results_field = 'objects'

## Using your custom pagination serializer

To have your custom pagination serializer be used by default, use the `DEFAULT_PAGINATION_SERIALIZER_CLASS` setting:

    REST_FRAMEWORK = {
        'DEFAULT_PAGINATION_SERIALIZER_CLASS':
            'example_app.pagination.CustomPaginationSerializer',
    }

Alternatively, to set your custom pagination serializer on a per-view basis, use the `pagination_serializer_class` attribute on a generic class based view:

    class PaginatedListView(generics.ListAPIView):
        model = ExampleModel
        pagination_serializer_class = CustomPaginationSerializer
        paginate_by = 10

# Third party packages

The following third party packages are also available.

## DRF-extensions

The [`DRF-extensions` package][drf-extensions] includes a [`PaginateByMaxMixin` mixin class][paginate-by-max-mixin] that allows your API clients to specify `?page_size=max` to obtain the maximum allowed page size.

[cite]: https://docs.djangoproject.com/en/dev/topics/pagination/
[drf-extensions]: http://chibisov.github.io/drf-extensions/docs/
[paginate-by-max-mixin]: http://chibisov.github.io/drf-extensions/docs/#paginatebymaxmixin