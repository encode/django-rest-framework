<a class="github" href="views.py"></a>

> Django's class based views are a welcome departure from the old-style views.
>
> &mdash; [Reinout van Rees][cite]

# Views

REST framework provides a simple `APIView` class, built on Django's `django.generics.views.View`.  The `APIView` class ensures five main things:

1. Any requests inside the view will become `Request` instances.
2. `Request` instances will have their `renderers` and `authentication` attributes automatically set. 
3. `Response` instances will have their `parsers` and `serializer` attributes automatically set.
4. `APIException` exceptions will be caught and return appropriate responses.
5. Any permissions provided will be checked prior to passing the request to a handler method.

Additionally there are a some minor extras, such as providing a default `options` handler, setting some common headers on the response prior to return, and providing the useful `initial()` and `final()` hooks.

## APIView

## Method handlers

Describe that APIView handles regular .get(), .post(), .put(), .delete() etc...

## .initial(request, *args, **kwargs)

## .final(request, response, *args, **kwargs)

## .parsers

## .renderers

## .serializer

## .authentication

## .permissions

## .headers

[cite]: http://reinout.vanrees.org/weblog/2011/08/24/class-based-views-usage.html