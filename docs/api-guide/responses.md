<a class="github" href="response.py"></a>

# Responses

> Unlike basic HttpResponse objects, TemplateResponse objects retain the details of the context that was provided by the view to compute the response. The final output of the response is not computed until it is needed, later in the response process.
>
> &mdash; [Django documentation][cite]

REST framework supports HTTP content negotiation by providing a `Response` class which allows you to return content that can be rendered into multiple content types, depending on the client request.

The `Response` class subclasses Django's `SimpleTemplateResponse`.  `Response` objects are initialised with data, which should consist of native python primatives.  REST framework then uses standard HTTP content negotiation to determine how it should render the final response content.

There's no requirement for you to use the `Response` class, you can also return regular `HttpResponse` objects from your views if you want, but it provides a nicer interface for returning Web API responses.

Unless you want to heavily customize REST framework for some reason, you should always use an `APIView` class or `@api_view` function for views that return `Response` objects.  Doing so ensures that the view can perform content negotiation and select the appropriate renderer for the response, before it is returned from the view.

## Response(data, status=None, headers=None)

Unlike regular `HttpResponse` objects, you do not instantiate `Response` objects with rendered content.  Instead you pass in unrendered data, which may consist of any python primatives.

The renderers used by the `Response` class cannot natively handle complex datatypes such as Django model instances, so you need to serialize the data into primative datatypes before creating the `Response` object.

You can use REST framework's `Serializer` classes to perform this data serialization, or use your own custom serialization.

## .data

The unrendered content of a `Request` object can be accessed using the `.data` attribute.

## .content

To access the rendered content of a `Response` object, you must first call `.render()`.  You'll typically only need to do this in cases such as unit testing responses - when you return a `Response` from a view Django's response cycle will handle calling `.render()` for you.

## .renderer

When you return a `Response` instance, the `APIView` class or `@api_view` decorator will select the appropriate renderer, and set the `.renderer` attribute on the `Response`, before returning it from the view.

[cite]: https://docs.djangoproject.com/en/dev/ref/template-response/