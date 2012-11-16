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
            username = self.request.QUERY_PARAMS.get('username', None)
            if username is not None:
                queryset = queryset.filter(purchaser__username=username)
            return queryset

---

# Generic Filtering

As well as being able to override the default queryset, REST framework also includes support for generic filtering backends that allow you to easily construct complex filters that can be specified by the client using query parameters.

REST framework supports pluggable backends to implement filtering, and provides an implementation which uses the [django-filter] package.

To use REST framework's filtering backend, first install `django-filter`.

    pip install django-filter

You must also set the filter backend to `DjangoFilterBackend` in your settings:

    REST_FRAMEWORK = {
        'FILTER_BACKEND': 'rest_framework.filters.DjangoFilterBackend'
    }


## Specifying filter fields

If all you need is simple equality-based filtering, you can set a `filter_fields` attribute on the view, listing the set of fields you wish to filter against.

    class ProductList(generics.ListAPIView):
        model = Product
        serializer_class = ProductSerializer
        filter_fields = ('category', 'in_stock')

This will automatically create a `FilterSet` class for the given fields, and will allow you to make requests such as:

    http://example.com/api/products?category=clothing&in_stock=True

## Specifying a FilterSet

For more advanced filtering requirements you can specify a `FilterSet` class that should be used by the view.  For example:

    class ProductFilter(django_filters.FilterSet):
        min_price = django_filters.NumberFilter(lookup_type='gte')
        max_price = django_filters.NumberFilter(lookup_type='lte')
        class Meta:
            model = Product
            fields = ['category', 'in_stock', 'min_price', 'max_price']

    class ProductList(generics.ListAPIView):
        model = Product
        serializer_class = ProductSerializer
        filter_class = ProductFilter

Which will allow you to make requests such as:

    http://example.com/api/products?category=clothing&max_price=10.00

For more details on using filter sets see the [django-filter documentation][django-filter-docs].

---

**Hints & Tips**

* By default filtering is not enabled.  If you want to use `DjangoFilterBackend` remember to make sure it is installed by using the `'FILTER_BACKEND'` setting.
* When using boolean fields, you should use the values `True` and `False` in the URL query parameters, rather than `0`, `1`, `true` or `false`.  (The allowed boolean values are currently hardwired in Django's [NullBooleanSelect implementation][nullbooleanselect].) 
* `django-filter` supports filtering across relationships, using Django's double-underscore syntax.

---

## Overriding the initial queryset
 
Note that you can use both an overridden `.get_queryset()` and generic filtering together, and everything will work as expected.  For example, if `Product` had a many-to-many relationship with `User`, named `purchase`, you might want to write a view like this:

    class PurchasedProductsList(generics.ListAPIView):
        """
        Return a list of all the products that the authenticated
        user has ever purchased, with optional filtering.
        """
        model = Product
        serializer_class = ProductSerializer
        filter_class = ProductFilter
        
        def get_queryset(self):
            user = self.request.user
            return user.purchase_set.all()
---

# Custom generic filtering

You can also provide your own generic filtering backend, or write an installable app for other developers to use.

To do so override `BaseFilterBackend`, and override the `.filter_queryset(self, request, queryset, view)` method.  The method should return a new, filtered queryset.

To install the filter backend, set the `'FILTER_BACKEND'` key in your `'REST_FRAMEWORK'` setting, using the dotted import path of the filter backend class.

For example:

    REST_FRAMEWORK = {
        'FILTER_BACKEND': 'custom_filters.CustomFilterBackend'
    }

[cite]: https://docs.djangoproject.com/en/dev/topics/db/queries/#retrieving-specific-objects-with-filters
[django-filter]: https://github.com/alex/django-filter
[django-filter-docs]: https://django-filter.readthedocs.org/en/latest/index.html
[nullbooleanselect]: https://github.com/django/django/blob/master/django/forms/widgets.py