Views
=====

REST framework provides a simple `View` class, built on Django's `django.generics.views.View`.  The `View` class ensures five main things:

1. Any requests inside the view will become `Request` instances.
2. `Request` instances will have their `renderers` and `authentication` attributes automatically set. 
3. `Response` instances will have their `parsers` and `serializer` attributes automatically set.
4. `ImmediateResponse` exceptions will be caught and returned as regular responses.
5. Any permissions provided will be checked prior to passing the request to a handler method.

Additionally there are a some minor extras, such as providing a default `options` handler, setting some common headers on the response prior to return, and providing the useful `initial()` and `final()` hooks.

View
----

.get(), .post(), .put(), .delete() etc...
-----------------------------------------

.initial(request, *args, **kwargs)
----------------------------------

.final(request, response, *args, **kwargs)
------------------------------------------

.parsers
--------

.renderers
----------

.serializer
-----------

.authentication
---------------

.permissions
------------

.headers
--------

