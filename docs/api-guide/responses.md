<a class="github" href="response.py"></a>

# Responses

> Unlike basic HttpResponse objects, TemplateResponse objects retain the details of the context that was provided by the view to compute the response. The final output of the response is not computed until it is needed, later in the response process.
>
> &mdash; [Django documentation][cite]

REST framework supports HTTP content negotiation by providing a `Response` class which allows you to return content that can be rendered into multiple content types, depending on the client request.

The `Response` class subclasses Django's `SimpleTemplateResponse`.  `Response` objects are initialised with data, which should consist of native python primatives.  REST framework then uses standard HTTP content negotiation to determine how it should render the final response content.

There's no requirement for you to use the `Response` class, you can also return regular `HttpResponse` objects from your views if you want, but it provides a nicer interface for returning Web API responses.

Unless you want to heavily customize REST framework for some reason, you should always use an `APIView` class or `@api_view` function for views that return `Response` objects.  Doing so ensures that the view can perform content negotiation and select the appropriate renderer for the response, before it is returned from the view.

---

# Methods

## Response(data, status=None, template_name=None, headers=None)

Unlike regular `HttpResponse` objects, you do not instantiate `Response` objects with rendered content.  Instead you pass in unrendered data, which may consist of any python primatives.

The renderers used by the `Response` class cannot natively handle complex datatypes such as Django model instances, so you need to serialize the data into primative datatypes before creating the `Response` object.

You can use REST framework's `Serializer` classes to perform this data serialization, or use your own custom serialization.

Arguments:

* `data`: The serialized data for the response.
* `status`: A status code for the response.  Defaults to 200.  See also [status codes][statuscodes].
* `template_name`: A template name to use if `HTMLTemplateRenderer` is selected.
* `headers`: A dictionary of HTTP headers to use in the response.

## .render()

This methd is called to render the serialized data of the response into the final response content.  When `.render()` is called, the response content will be set to the result of calling the `.render(data, accepted_media_type)` method on the accepted renderer instance.

You won't typically need to call `.render()` yourself, as it's handled by Django's standard response cycle.

## Standard HTTPResponse methods

The `Response` class extends `SimpleTemplateResponse`, and all the usual methods are also available on the response.  For example you can set headers on the response in the standard way:

    response = Response()
    response['Cache-Control'] = 'no-cache'

---

# Attributes

## .data

The unrendered content of a `Request` object can be accessed using the `.data` attribute.

## .status_code

The numeric status code of the HTTP response.

## .content

The rendered content of the response.  `.render()` must have been called before `.content` can be accessed.

## .template_name

The `template_name`, if supplied.  Only required if `HTMLTemplateRenderer` or some other custom template renderer is the accepted renderer for the reponse.

## .accepted_renderer

The renderer instance that will be used to render the response.

Set automatically by the `APIView` or `@api_view` immediately before the response is returned from the view.

## .accepted_media_type

The media type that was selected by the content negotiation stage.

Set automatically by the `APIView` or `@api_view` immediately before the response is returned from the view.


[cite]: https://docs.djangoproject.com/en/dev/ref/template-response/
[statuscodes]: status-codes.md