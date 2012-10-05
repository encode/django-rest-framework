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
        
        def get_paginate_by(self):
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

## ListAPIView

Used for read-only endpoints to represent a collection of model instances.

Provides a `get` method handler.

Extends: [MultipleObjectBaseAPIView], [ListModelMixin]

## ListCreateAPIView

Used for read-write endpoints to represent a collection of model instances.

Provides `get` and `post` method handlers.

Extends: [MultipleObjectBaseAPIView], [ListModelMixin], [CreateModelMixin]

## RetrieveAPIView

Used for read-only endpoints to represent a single model instance.

Provides a `get` method handler.

Extends: [SingleObjectBaseAPIView], [RetrieveModelMixin]

## RetrieveUpdateDestroyAPIView

Used for read-write endpoints to represent a single model instance.

Provides `get`, `put` and `delete` method handlers.

Extends: [SingleObjectBaseAPIView], [RetrieveModelMixin], [UpdateModelMixin], [DestroyModelMixin]

---

# Base views

Each of the generic views provided is built by combining one of the base views below, with one or more mixin classes.

## BaseAPIView

Extends REST framework's `APIView` class, adding support for serialization of model instances and model querysets.

## MultipleObjectBaseAPIView

Provides a base view for acting on a single object, by combining REST framework's `APIView`, and Django's [MultipleObjectMixin].

**See also:** ccbv.co.uk documentation for [MultipleObjectMixin][multiple-object-mixin-classy].

## SingleObjectBaseAPIView

Provides a base view for acting on a single object, by combining REST framework's `APIView`, and Django's [SingleObjectMixin].

**See also:** ccbv.co.uk documentation for [SingleObjectMixin][single-object-mixin-classy].

---

# Mixins

The mixin classes provide the actions that are used to provide the basic view behaviour.  Note that the mixin classes provide action methods rather than defining the handler methods such as `.get()` and `.post()` directly.  This allows for more flexible composition of behaviour. 

## ListModelMixin

Provides a `.list(request, *args, **kwargs)` method, that implements listing a queryset.

## CreateModelMixin

Provides a `.create(request, *args, **kwargs)` method, that implements creating and saving a new model instance.

## RetrieveModelMixin

Provides a `.retrieve(request, *args, **kwargs)` method, that implements returning an existing model instance in a response.

## UpdateModelMixin

Provides a `.update(request, *args, **kwargs)` method, that implements updating and saving an existing model instance.

## DestroyModelMixin

Provides a `.destroy(request, *args, **kwargs)` method, that implements deletion of an existing model instance.

[cite]: https://docs.djangoproject.com/en/dev/ref/class-based-views/#base-vs-generic-views
[MultipleObjectMixin]: https://docs.djangoproject.com/en/dev/ref/class-based-views/mixins-multiple-object/
[SingleObjectMixin]: https://docs.djangoproject.com/en/dev/ref/class-based-views/mixins-single-object/
[multiple-object-mixin-classy]: http://ccbv.co.uk/projects/Django/1.4/django.views.generic.list/MultipleObjectMixin/
[single-object-mixin-classy]: http://ccbv.co.uk/projects/Django/1.4/django.views.generic.detail/SingleObjectMixin/

[SingleObjectBaseAPIView]: #singleobjectbaseapiview
[MultipleObjectBaseAPIView]: #multipleobjectbaseapiview
[ListModelMixin]: #listmodelmixin
[CreateModelMixin]: #createmodelmixin
[RetrieveModelMixin]: #retrievemodelmixin
[UpdateModelMixin]: #updatemodelmixin
[DestroyModelMixin]: #destroymodelmixin