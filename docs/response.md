Responses
=========

> HTTP has provisions for several mechanisms for "content negotiation" -- the process of selecting the best representation for a given response when there are multiple representations available. -- RFC 2616, Fielding et al.

> Unlike basic HttpResponse objects, TemplateResponse objects retain the details of the context that was provided by the view to compute the response. The final output of the response is not computed until it is needed, later in the response process. -- Django documentation.

Django REST framework supports HTTP content negotiation by providing a `Response` class which allows you to return content that can be rendered into multiple content types, depending on the client request.

The `Response` class subclasses Django's `TemplateResponse`.  It works by allowing you to specify a serializer and a number of different renderers.  REST framework then uses standard HTTP content negotiation to determine how it should render the final response content.

There's no requirement for you to use the `Response` class, you can also return regular `HttpResponse` objects from your views if you want, but it does provide a better interface for returning Web API responses.

Response(content, status, headers=None, serializer=None, renderers=None, format=None)
-------------------------------------------------------------------------------------

serializer
----------

renderers
---------

view
----

ImmediateResponse(...)
----------------------