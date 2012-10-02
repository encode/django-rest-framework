<a class="github" href="mixins.py"></a>
<a class="github" href="generics.py"></a>

# Generic views

> Django’s generic views... were developed as a shortcut for common usage patterns... They take certain common idioms and patterns found in view development and abstract them so that you can quickly write common views of data without having to repeat yourself.
>
> &mdash; [Django Documentation][cite]

One of the key benefits of class based views is the way they allow you to compose bits of reusable behaviour.  REST framework takes advantage of this by providing a number of pre-built views that provide for commonly used patterns. 

## Example

...

---

# API Reference

## ListAPIView

Used for read-write endpoints to represent a collection of model instances.

Provides a `get` method handler.

## ListCreateAPIView

Used for read-write endpoints to represent a collection of model instances.

Provides `get` and `post` method handlers.

## RetrieveAPIView

Used for read-only endpoints to represent a single model instance.

Provides a `get` method handler.

## RetrieveUpdateDestroyAPIView

Used for read-write endpoints to represent a single model instance.

Provides `get`, `put` and `delete` method handlers.

---

# Base views

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

The mixin classes provide the actions that are used 

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

## MetadataMixin

Provides a `.metadata(request, *args, **kwargs)` method, that returns a response containing metadata about the view.

[cite]: https://docs.djangoproject.com/en/dev/ref/class-based-views/#base-vs-generic-views
[MultipleObjectMixin]: https://docs.djangoproject.com/en/dev/ref/class-based-views/mixins-multiple-object/
[SingleObjectMixin]: https://docs.djangoproject.com/en/dev/ref/class-based-views/mixins-single-object/
[multiple-object-mixin-classy]: http://ccbv.co.uk/projects/Django/1.4/django.views.generic.list/MultipleObjectMixin/
[single-object-mixin-classy]: http://ccbv.co.uk/projects/Django/1.4/django.views.generic.detail/SingleObjectMixin/
