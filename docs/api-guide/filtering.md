<a class="github" href="filters.py"></a>

# Filtering

> The root QuerySet provided by the Manager describes all objects in the database table. Usually, though, you'll need to select only a subset of the complete set of objects.
>
> &mdash; [Django documentation][cite]

The default behavior of REST framework's generic list views is to return the entire queryset for a model manager.  Often you will want your API to restrict the items that are returned by the queryset.

The simplest way to filter the queryset of any view that subclasses `MultipleObjectAPIView` is to override the `.get_queryset()` method.

Overriding this method allows you to customize the queryset returned by the view in a number of different ways.

## Filtering against the current user

You might want to filter the queryset to ensure that only results relevant to the currently authenticated user making the request are returned.

You can do so by filtering based on the value of `request.user`.

For example:

    class PurchaseList(generics.ListAPIView)
        model = Purchase
        serializer_class = PurchaseSerializer
 
        def get_queryset(self):
            """
            This view should return a list of all the purchases
            for the currently authenticated user.
            """
            user = self.request.user
            return Purchase.objects.filter(purchaser=user)       


## Filtering against the URL

Another style of filtering might involve restricting the queryset based on some part of the URL.  

For example if your URL config contained an entry like this:

    url('^purchases/(?P<username>.+)/$', PurchaseList.as_view()),

You could then write a view that returned a purchase queryset filtered by the username portion of the URL:

    class PurchaseList(generics.ListAPIView)
        model = Purchase
        serializer_class = PurchaseSerializer
 
        def get_queryset(self):
            """
            This view should return a list of all the purchases for
            the user as determined by the username portion of the URL.
            """
            username = self.kwargs['username']
            return Purchase.objects.filter(purchaser__username=username)

## Filtering against query parameters 

A final example of filtering the initial queryset would be to determine the initial queryset based on query parameters in the url.

We can override `.get_queryset()` to deal with URLs such as `http://example.com/api/purchases?username=denvercoder9`, and filter the queryset only if the `username` parameter is included in the URL:

    class PurchaseList(generics.ListAPIView)
        model = Purchase
        serializer_class = PurchaseSerializer
 
        def get_queryset(self):
            """
            Optionally restricts the returned purchases to a given user,
            by filtering against a `username` query parameter in the URL.
            """
            queryset = Purchase.objects.all()
            username = self.request.QUERY_PARAMS.get('username', None):
            if username is not None:
                queryset = queryset.filter(purchaser__username=username)
            return queryset

---

# Generic Filtering

As well as being able to override the default queryset, REST framework also includes support for generic filtering backends that allow you to easily construct complex filters that can be specified by the client using query parameters.

REST framework supports pluggable backends to implement filtering, and includes a default implementation which uses the [django-filter] package.

To use REST framework's default filtering backend, first install `django-filter`.

    pip install -e git+https://github.com/alex/django-filter.git#egg=django-filter

**Note**: The currently supported version of `django-filter` is the `master` branch.  A PyPI release is expected to be coming soon.

## Specifying filter fields

**TODO**: Document setting `.filter_fields` on the view.

## Specifying a FilterSet

**TODO**: Document setting `.filter_class` on the view.

**TODO**: Note support for `lookup_type`, double underscore relationship spanning, and ordering.

**TODO**: Note that overiding `get_queryset()` can be used together with generic filtering 

---

# Custom generic filtering

You can also provide your own generic filtering backend, or write an installable app for other developers to use.

To do so overide `BaseFilterBackend`, and override the `.filter_queryset(self, request, queryset, view)` method.

To install the filter, set the `'FILTER_BACKEND'` key in your `'REST_FRAMEWORK'` setting, using the dotted import path of the filter backend class.

For example:

    REST_FRAMEWORK = {
        'FILTER_BACKEND': 'custom_filters.CustomFilterBackend'
    }

[cite]: https://docs.djangoproject.com/en/dev/topics/db/queries/#retrieving-specific-objects-with-filters
[django-filter]: https://github.com/alex/django-filter