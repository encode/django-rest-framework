<a class="github" href="mixins.py"></a>
<a class="github" href="generics.py"></a>

# Generic views

> Django’s generic views... were developed as a shortcut for common usage patterns... They take certain common idioms and patterns found in view development and abstract them so that you can quickly write common views of data without having to repeat yourself.
>
> &mdash; [Django Documentation][cite]

One of the key benefits of class based views is the way they allow you to compose bits of reusable behaviour.  REST framework takes advantage of this by providing a number of pre-built views that provide for commonly used patterns. 

The generic views provided by REST framework allow you to quickly build API views that map closely to your database models.

If the generic views don't suit the needs of your API, you can drop down to using the regular `APIView` class, or reuse the mixins and base classes used by the generic views to compose your own set of reusable generic views. 

## Examples

Typically when using the generic views, you'll override the view, and set several class attributes.

    class UserList(generics.ListCreateAPIView):
        model = User
        serializer_class = UserSerializer
        permission_classes = (IsAdminUser,)
        paginate_by = 100

For more complex cases you might also want to override various methods on the view class.  For example.

    class UserList(generics.ListCreateAPIView):
        model = User
        serializer_class = UserSerializer
        permission_classes = (IsAdminUser,)
        
        def get_paginate_by(self, queryset):
            """
            Use smaller pagination for HTML representations.
            """
            page_size_param = self.request.QUERY_PARAMS.get('page_size')
            if page_size_param:
                return int(page_size_param)
            return 100

For very simple cases you might want to pass through any class attributes using the `.as_view()` method.  For example, your URLconf might include something the following entry.

    url(r'^/users/', ListCreateAPIView.as_view(model=User) name='user-list')

---

# API Reference

The following classes are the concrete generic views.  If you're using generic views this is normally the level you'll be working at unless you need heavily customized behavior.

## CreateAPIView

Used for **create-only** endpoints.

Provides `post` method handlers.

Extends: [GenericAPIView], [CreateModelMixin]

## ListAPIView

Used for **read-only** endpoints to represent a **collection of model instances**.

Provides a `get` method handler.

Extends: [MultipleObjectAPIView], [ListModelMixin]

## RetrieveAPIView

Used for **read-only** endpoints to represent a **single model instance**.

Provides a `get` method handler.

Extends: [SingleObjectAPIView], [RetrieveModelMixin]

## DestroyAPIView

Used for **delete-only** endpoints for a **single model instance**.

Provides a `delete` method handler.

Extends: [SingleObjectAPIView], [DestroyModelMixin]

## UpdateAPIView

Used for **update-only** endpoints for a **single model instance**.

Provides a `put` method handler.

Extends: [SingleObjectAPIView], [UpdateModelMixin]

## ListCreateAPIView

Used for **read-write** endpoints to represent a **collection of model instances**.

Provides `get` and `post` method handlers.

Extends: [MultipleObjectAPIView], [ListModelMixin], [CreateModelMixin]

## RetrieveDestroyAPIView

Used for **read or delete** endpoints to represent a **single model instance**.

Provides `get` and `delete` method handlers.

Extends: [SingleObjectAPIView], [RetrieveModelMixin], [DestroyModelMixin]

## RetrieveUpdateDestroyAPIView

Used for **read-write-delete** endpoints to represent a **single model instance**.

Provides `get`, `put` and `delete` method handlers.

Extends: [SingleObjectAPIView], [RetrieveModelMixin], [UpdateModelMixin], [DestroyModelMixin]

---

# Base views

Each of the generic views provided is built by combining one of the base views below, with one or more mixin classes.

## GenericAPIView

Extends REST framework's `APIView` class, adding support for serialization of model instances and model querysets.

**Attributes**:

* `model` - The model that should be used for this view.  Used as a fallback for determining the serializer if `serializer_class` is not set, and as a fallback for determining the queryset if `queryset` is not set.  Otherwise not required.
* `serializer_class` - The serializer class that should be used for validating and deserializing input, and for serializing output.  If unset, this defaults to creating a serializer class using `self.model`, with the `DEFAULT_MODEL_SERIALIZER_CLASS` setting as the base serializer class.

## MultipleObjectAPIView

Provides a base view for acting on a single object, by combining REST framework's `APIView`, and Django's [MultipleObjectMixin].

**See also:** ccbv.co.uk documentation for [MultipleObjectMixin][multiple-object-mixin-classy].

**Attributes**:

* `queryset` - The queryset that should be used for returning objects from this view.  If unset, defaults to the default queryset manager for `self.model`.
* `paginate_by` - The size of pages to use with paginated data.  If set to `None` then pagination is turned off.  If unset this uses the same value as the `PAGINATE_BY` setting, which defaults to `None`.
* `paginate_by_param` - The name of a query parameter, which can be used by the client to overide the default page size to use for pagination.  If unset this uses the same value as the `PAGINATE_BY_PARAM` setting, which defaults to `None`.

## SingleObjectAPIView

Provides a base view for acting on a single object, by combining REST framework's `APIView`, and Django's [SingleObjectMixin].

**See also:** ccbv.co.uk documentation for [SingleObjectMixin][single-object-mixin-classy].

**Attributes**:

* `queryset` - The queryset that should be used when retrieving an object from this view.  If unset, defaults to the default queryset manager for `self.model`.
* `pk_kwarg` - The URL kwarg that should be used to look up objects by primary key. Defaults to `'pk'`. [Can only be set to non-default on Django 1.4+]
* `slug_kwarg` - The URL kwarg that should be used to look up objects by a slug. Defaults to `'slug'`.  [Can only be set to non-default on Django 1.4+]
* `slug_field` - The field on the model that should be used to look up objects by a slug.  If used, this should typically be set to a field with `unique=True`. Defaults to `'slug'`.

---

# Mixins

The mixin classes provide the actions that are used to provide the basic view behaviour.  Note that the mixin classes provide action methods rather than defining the handler methods such as `.get()` and `.post()` directly.  This allows for more flexible composition of behaviour. 

## ListModelMixin

Provides a `.list(request, *args, **kwargs)` method, that implements listing a queryset.

If the queryset is populated, this returns a `200 OK` response, with a serialized representation of the queryset as the body of the response.  The response data may optionally be paginated.

If the queryset is empty this returns a `200 OK` reponse, unless the `.allow_empty` attribute on the view is set to `False`, in which case it will return a `404 Not Found`.

Should be mixed in with [MultipleObjectAPIView].

## CreateModelMixin

Provides a `.create(request, *args, **kwargs)` method, that implements creating and saving a new model instance.

If an object is created this returns a `201 Created` response, with a serialized representation of the object as the body of the response.  If the representation contains a key named `url`, then the `Location` header of the response will be populated with that value.

If the request data provided for creating the object was invalid, a `400 Bad Request` response will be returned, with the error details as the body of the response.

Should be mixed in with any [GenericAPIView].

## RetrieveModelMixin

Provides a `.retrieve(request, *args, **kwargs)` method, that implements returning an existing model instance in a response.

If an object can be retrieve this returns a `200 OK` response, with a serialized representation of the object as the body of the response.  Otherwise it will return a `404 Not Found`.

Should be mixed in with [SingleObjectAPIView].

## UpdateModelMixin

Provides a `.update(request, *args, **kwargs)` method, that implements updating and saving an existing model instance.

If an object is updated this returns a `200 OK` response, with a serialized representation of the object as the body of the response.

If an object is created, for example when making a `DELETE` request followed by a `PUT` request to the same URL, this returns a `201 Created` response, with a serialized representation of the object as the body of the response.

If the request data provided for updating the object was invalid, a `400 Bad Request` response will be returned, with the error details as the body of the response.

Should be mixed in with [SingleObjectAPIView].

## DestroyModelMixin

Provides a `.destroy(request, *args, **kwargs)` method, that implements deletion of an existing model instance.

If an object is deleted this returns a `204 No Content` response, otherwise it will return a `404 Not Found`.

Should be mixed in with [SingleObjectAPIView].

[cite]: https://docs.djangoproject.com/en/dev/ref/class-based-views/#base-vs-generic-views
[MultipleObjectMixin]: https://docs.djangoproject.com/en/dev/ref/class-based-views/mixins-multiple-object/
[SingleObjectMixin]: https://docs.djangoproject.com/en/dev/ref/class-based-views/mixins-single-object/
[multiple-object-mixin-classy]: http://ccbv.co.uk/projects/Django/1.4/django.views.generic.list/MultipleObjectMixin/
[single-object-mixin-classy]: http://ccbv.co.uk/projects/Django/1.4/django.views.generic.detail/SingleObjectMixin/

[GenericAPIView]: #genericapiview
[SingleObjectAPIView]: #singleobjectapiview
[MultipleObjectAPIView]: #multipleobjectapiview
[ListModelMixin]: #listmodelmixin
[CreateModelMixin]: #createmodelmixin
[RetrieveModelMixin]: #retrievemodelmixin
[UpdateModelMixin]: #updatemodelmixin
[DestroyModelMixin]: #destroymodelmixin