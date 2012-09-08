<a class="github" href="response.py"></a>

# Responses

> Unlike basic HttpResponse objects, TemplateResponse objects retain the details of the context that was provided by the view to compute the response. The final output of the response is not computed until it is needed, later in the response process.
>
> &mdash; [Django documentation][cite]

REST framework supports HTTP content negotiation by providing a `Response` class which allows you to return content that can be rendered into multiple content types, depending on the client request.

The `Response` class subclasses Django's `TemplateResponse`.  `Response` objects are initialised with content, which should consist of native python primatives.  REST framework then uses standard HTTP content negotiation to determine how it should render the final response content.

There's no requirement for you to use the `Response` class, you can also return regular `HttpResponse` objects from your views if you want, but it does provide a better interface for returning Web API responses.

## Response(content, headers=None,  renderers=None, view=None, format=None, status=None)


## .renderers

## .view

## .format


[cite]: https://docs.djangoproject.com/en/dev/ref/template-response/