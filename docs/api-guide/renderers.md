<a class="github" href="renderers.py"></a>

# Renderers

> Before a TemplateResponse instance can be returned to the client, it must be rendered. The rendering process takes the intermediate representation of template and context, and turns it into the final byte stream that can be served to the client.
>
> &mdash; [Django documentation][cite]

REST framework includes a number of built in Renderer classes, that allow you to return responses with various media types.  There is also support for defining your own custom renderers, which gives you the flexibility to design your own media types.

## How the renderer is determined

The set of valid renderers for a view is always defined as a list of classes.  When a view is entered REST framework will perform content negotiation on the incoming request, and determine the most appropriate renderer to satisfy the request.

The basic process of content negotiation involves examining the request's `Accept` header, to determine which media types it expects in the response.  Optionally, format suffixes on the URL may be used to explicitly request a particular representation.  For example the URL `http://example.com/api/users_count.json` might be an endpoint that always returns JSON data.

For more information see the documentation on [content negotiation][conneg].

## Setting the renderers

The default set of renderers may be set globally, using the `DEFAULT_RENDERER_CLASSES` setting.  For example, the following settings would use `YAML` as the main media type and also include the self describing API.

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.YAMLRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        )
    }

You can also set the renderers used for an individual view, or viewset,
using the `APIView` class based views.

    from django.contrib.auth.models import User
    from rest_framework.renderers import JSONRenderer, YAMLRenderer
    from rest_framework.response import Response
    from rest_framework.views import APIView

    class UserCountView(APIView):
        """
        A view that returns the count of active users, in JSON or YAML.
        """
        renderer_classes = (JSONRenderer, YAMLRenderer)

        def get(self, request, format=None):
            user_count = User.objects.filter(active=True).count()
            content = {'user_count': user_count}
            return Response(content)

Or, if you're using the `@api_view` decorator with function based views.

    @api_view(['GET'])
    @renderer_classes((JSONRenderer, JSONPRenderer))
    def user_count_view(request, format=None):
        """
        A view that returns the count of active users, in JSON or JSONp.
        """
        user_count = User.objects.filter(active=True).count()
        content = {'user_count': user_count}
        return Response(content)

## Ordering of renderer classes

It's important when specifying the renderer classes for your API to think about what priority you want to assign to each media type.  If a client underspecifies the representations it can accept, such as sending an `Accept: */*` header, or not including an `Accept` header at all, then REST framework will select the first renderer in the list to use for the response.

For example if your API serves JSON responses and the HTML browsable API, you might want to make `JSONRenderer` your default renderer, in order to send `JSON` responses to clients that do not specify an `Accept` header.

If your API includes views that can serve both regular webpages and API responses depending on the request, then you might consider making `TemplateHTMLRenderer` your default renderer, in order to play nicely with older browsers that send [broken accept headers][browser-accept-headers].

---

# API Reference

## JSONRenderer

Renders the request data into `JSON`, using utf-8 encoding.

Note that non-ascii characters will be rendered using JSON's `\uXXXX` character escape.  For example:

    {"unicode black star": "\u2605"}

The client may additionally include an `'indent'` media type parameter, in which case the returned `JSON` will be indented.  For example `Accept: application/json; indent=4`.

    {
        "unicode black star": "\u2605"
    }

**.media_type**: `application/json`

**.format**: `'.json'`

**.charset**: `None`

## UnicodeJSONRenderer

Renders the request data into `JSON`, using utf-8 encoding.

Note that non-ascii characters will not be character escaped.  For example:

    {"unicode black star": "★"}

The client may additionally include an `'indent'` media type parameter, in which case the returned `JSON` will be indented.  For example `Accept: application/json; indent=4`.

    {
        "unicode black star": "★"
    }

Both the `JSONRenderer` and `UnicodeJSONRenderer` styles conform to [RFC 4627][rfc4627], and are syntactically valid JSON.

**.media_type**: `application/json`

**.format**: `'.json'`

**.charset**: `None`

## JSONPRenderer

Renders the request data into `JSONP`.  The `JSONP` media type provides a mechanism of allowing cross-domain AJAX requests, by wrapping a `JSON` response in a javascript callback.

The javascript callback function must be set by the client including a `callback` URL query parameter.  For example `http://example.com/api/users?callback=jsonpCallback`.  If the callback function is not explicitly set by the client it will default to `'callback'`.

---

**Warning**: If you require cross-domain AJAX requests, you should almost certainly be using the more modern approach of [CORS][cors] as an alternative to `JSONP`.  See the [CORS documentation][cors-docs] for more details.

The `jsonp` approach is essentially a browser hack, and is [only appropriate for globally  readable API endpoints][jsonp-security], where `GET` requests are unauthenticated and do not require any user permissions.

---

**.media_type**: `application/javascript`

**.format**: `'.jsonp'`

**.charset**: `utf-8`

## YAMLRenderer

Renders the request data into `YAML`. 

Requires the `pyyaml` package to be installed.

**.media_type**: `application/yaml`

**.format**: `'.yaml'`

**.charset**: `utf-8`

## XMLRenderer

Renders REST framework's default style of `XML` response content.

Note that the `XML` markup language is used typically used as the base language for more strictly defined domain-specific languages, such as `RSS`, `Atom`, and `XHTML`.

If you are considering using `XML` for your API, you may want to consider implementing a custom renderer and parser for your specific requirements, and using an existing domain-specific media-type, or creating your own custom XML-based media-type.

**.media_type**: `application/xml`

**.format**: `'.xml'`

**.charset**: `utf-8`

## TemplateHTMLRenderer

Renders data to HTML, using Django's standard template rendering.
Unlike other renderers, the data passed to the `Response` does not need to be serialized.  Also, unlike other renderers, you may want to include a `template_name` argument when creating the `Response`.

The TemplateHTMLRenderer will create a `RequestContext`, using the `response.data` as the context dict, and determine a template name to use to render the context.

The template name is determined by (in order of preference):

1. An explicit `template_name` argument passed to the response.
2. An explicit `.template_name` attribute set on this class.
3. The return result of calling `view.get_template_names()`.

An example of a view that uses `TemplateHTMLRenderer`:

    class UserDetail(generics.RetrieveAPIView):
        """
        A view that returns a templated HTML representations of a given user.
        """
        queryset = User.objects.all()
        renderer_classes = (TemplateHTMLRenderer,)

        def get(self, request, *args, **kwargs):
            self.object = self.get_object()
            return Response({'user': self.object}, template_name='user_detail.html')
 
You can use `TemplateHTMLRenderer` either to return regular HTML pages using REST framework, or to return both HTML and API responses from a single endpoint.

If you're building websites that use `TemplateHTMLRenderer` along with other renderer classes, you should consider listing `TemplateHTMLRenderer` as the first class in the `renderer_classes` list, so that it will be prioritised first even for browsers that send poorly formed `ACCEPT:` headers.

**.media_type**: `text/html`

**.format**: `'.html'`

**.charset**: `utf-8`

See also: `StaticHTMLRenderer`

## StaticHTMLRenderer

A simple renderer that simply returns pre-rendered HTML.  Unlike other renderers, the data passed to the response object should be a string representing the content to be returned.

An example of a view that uses `TemplateHTMLRenderer`:

    @api_view(('GET',))
    @renderer_classes((StaticHTMLRenderer,))
    def simple_html_view(request): 
        data = '<html><body><h1>Hello, world</h1></body></html>'
        return Response(data)

You can use `TemplateHTMLRenderer` either to return regular HTML pages using REST framework, or to return both HTML and API responses from a single endpoint.

**.media_type**: `text/html`

**.format**: `'.html'`

**.charset**: `utf-8`

See also: `TemplateHTMLRenderer`

## HTMLFormRenderer

Renders data returned by a serializer into an HTML form.  The output of this renderer does not include the enclosing `<form>` tags or an submit actions, as you'll probably need those to include the desired method and URL.  Also note that the `HTMLFormRenderer` does not yet support including field error messages.

Note that the template used by the `HTMLFormRenderer` class, and the context submitted to it **may be subject to change**.  If you need to use this renderer class it is advised that you either make a local copy of the class and templates, or follow the release note on REST framework upgrades closely.

**.media_type**: `text/html`

**.format**: `'.form'`

**.charset**: `utf-8`

**.template**: `'rest_framework/form.html'`

## BrowsableAPIRenderer

Renders data into HTML for the Browsable API.  This renderer will determine which other renderer would have been given highest priority, and use that to display an API style response within the HTML page.

**.media_type**: `text/html`

**.format**: `'.api'`

**.charset**: `utf-8`

**.template**: `'rest_framework/api.html'`

#### Customizing BrowsableAPIRenderer

By default the response content will be rendered with the highest priority renderer apart from `BrowseableAPIRenderer`.  If you need to customize this behavior, for example to use HTML as the default return format, but use JSON in the browsable API, you can do so by overriding the `get_default_renderer()` method.  For example:

    class CustomBrowsableAPIRenderer(BrowsableAPIRenderer):
        def get_default_renderer(self, view):
            return JSONRenderer()

## MultiPartRenderer

This renderer is used for rendering HTML multipart form data.  **It is not suitable as a response renderer**, but is instead used for creating test requests, using REST framework's [test client and test request factory][testing].

**.media_type**: `multipart/form-data; boundary=BoUnDaRyStRiNg`

**.format**: `'.multipart'`

**.charset**: `utf-8`

---

# Custom renderers

To implement a custom renderer, you should override `BaseRenderer`, set the `.media_type` and `.format` properties, and implement the `.render(self, data, media_type=None, renderer_context=None)` method.

The method should return a bytestring, which will be used as the body of the HTTP response.

The arguments passed to the `.render()` method are:

### `data`

The request data, as set by the `Response()` instantiation.

### `media_type=None`

Optional.  If provided, this is the accepted media type, as determined by the content negotiation stage.

Depending on the client's `Accept:` header, this may be more specific than the renderer's `media_type` attribute, and may include media type parameters.  For example `"application/json; nested=true"`.

### `renderer_context=None`

Optional.  If provided, this is a dictionary of contextual information provided by the view.

By default this will include the following keys: `view`, `request`, `response`, `args`, `kwargs`.

## Example

The following is an example plaintext renderer that will return a response with the `data` parameter as the content of the response.

    from django.utils.encoding import smart_unicode
    from rest_framework import renderers


    class PlainTextRenderer(renderers.BaseRenderer):
        media_type = 'text/plain'
        format = 'txt'
        
        def render(self, data, media_type=None, renderer_context=None):
            return data.encode(self.charset)

## Setting the character set

By default renderer classes are assumed to be using the `UTF-8` encoding.  To use a different encoding, set the `charset` attribute on the renderer.

    class PlainTextRenderer(renderers.BaseRenderer):
        media_type = 'text/plain'
        format = 'txt'
        charset = 'iso-8859-1'

        def render(self, data, media_type=None, renderer_context=None):
            return data.encode(self.charset)

Note that if a renderer class returns a unicode string, then the response content will be coerced into a bytestring by the `Response` class, with the `charset` attribute set on the renderer used to determine the encoding.

If the renderer returns a bytestring representing raw binary content, you should set a charset value of `None`, which will ensure the `Content-Type` header of the response will not have a `charset` value set.

In some cases you may also want to set the `render_style` attribute to `'binary'`.  Doing so will also ensure that the browsable API will not attempt to display the binary content as a string.

    class JPEGRenderer(renderers.BaseRenderer):
        media_type = 'image/jpeg'
        format = 'jpg'
        charset = None
        render_style = 'binary'

        def render(self, data, media_type=None, renderer_context=None):
            return data

---

# Advanced renderer usage

You can do some pretty flexible things using REST framework's renderers.  Some examples...

* Provide either flat or nested representations from the same endpoint, depending on the requested media type.
* Serve both regular HTML webpages, and JSON based API responses from the same endpoints.
* Specify multiple types of HTML representation for API clients to use.
* Underspecify a renderer's media type, such as using `media_type = 'image/*'`, and use the `Accept` header to vary the encoding of the response. 

## Varying behaviour by media type

In some cases you might want your view to use different serialization styles depending on the accepted media type.  If you need to do this you can access `request.accepted_renderer` to determine the negotiated renderer that will be used for the response.

For example:

    @api_view(('GET',))
    @renderer_classes((TemplateHTMLRenderer, JSONRenderer))
    def list_users(request):
        """
        A view that can return JSON or HTML representations
        of the users in the system.
        """
        queryset = Users.objects.filter(active=True)

        if request.accepted_renderer.format == 'html':
            # TemplateHTMLRenderer takes a context dict,
            # and additionally requires a 'template_name'.
            # It does not require serialization.
            data = {'users': queryset}
            return Response(data, template_name='list_users.html')

        # JSONRenderer requires serialized data as normal.
        serializer = UserSerializer(instance=queryset)
        data = serializer.data
        return Response(data)

## Underspecifying the media type

In some cases you might want a renderer to serve a range of media types.
In this case you can underspecify the media types it should respond to, by using a `media_type` value such as `image/*`, or `*/*`.

If you underspecify the renderer's media type, you should make sure to specify the media type explicitly when you return the response, using the `content_type` attribute.  For example:

    return Response(data, content_type='image/png')

## Designing your media types

For the purposes of many Web APIs, simple `JSON` responses with hyperlinked relations may be sufficient.  If you want to fully embrace RESTful design and [HATEOAS] you'll need to consider the design and usage of your media types in more detail.

In [the words of Roy Fielding][quote], "A REST API should spend almost all of its descriptive effort in defining the media type(s) used for representing resources and driving application state, or in defining extended relation names and/or hypertext-enabled mark-up for existing standard media types.".

For good examples of custom media types, see GitHub's use of a custom [application/vnd.github+json] media type, and Mike Amundsen's IANA approved [application/vnd.collection+json] JSON-based hypermedia.

## HTML error views

Typically a renderer will behave the same regardless of if it's dealing with a regular response, or with a response caused by an exception being raised, such as an `Http404` or `PermissionDenied` exception, or a subclass of `APIException`.

If you're using either the `TemplateHTMLRenderer` or the `StaticHTMLRenderer` and an exception is raised, the behavior is slightly different, and mirrors [Django's default handling of error views][django-error-views].

Exceptions raised and handled by an HTML renderer will attempt to render using one of the following methods, by order of precedence.

* Load and render a template named `{status_code}.html`.
* Load and render a template named `api_exception.html`.
* Render the HTTP status code and text, for example "404 Not Found".

Templates will render with a `RequestContext` which includes the `status_code` and `details` keys.

**Note**: If `DEBUG=True`, Django's standard traceback error page will be displayed instead of rendering the HTTP status code and text.

---

# Third party packages

The following third party packages are also available.

## MessagePack

[MessagePack][messagepack] is a fast, efficient binary serialization format.  [Juan Riaza][juanriaza] maintains the [djangorestframework-msgpack][djangorestframework-msgpack] package which provides MessagePack renderer and parser support for REST framework.

## CSV

Comma-separated values are a plain-text tabular data format, that can be easily imported into spreadsheet applications.  [Mjumbe Poe][mjumbewu] maintains the [djangorestframework-csv][djangorestframework-csv] package which provides CSV renderer support for REST framework.

## UltraJSON

[UltraJSON][ultrajson] is an optimized C JSON encoder which can give significantly faster JSON rendering. [Jacob Haslehurst][hzy] maintains the [drf-ujson-renderer][drf-ujson-renderer] package which implements JSON rendering using the UJSON package.

## CamelCase JSON

[djangorestframework-camel-case] provides camel case JSON renderers and parsers for REST framework.  This allows serializers to use Python-style underscored field names, but be exposed in the API as Javascript-style camel case field names.  It is maintained by [Vitaly Babiy][vbabiy].


[cite]: https://docs.djangoproject.com/en/dev/ref/template-response/#the-rendering-process
[conneg]: content-negotiation.md
[browser-accept-headers]: http://www.gethifi.com/blog/browser-rest-http-accept-headers
[rfc4627]: http://www.ietf.org/rfc/rfc4627.txt
[cors]: http://www.w3.org/TR/cors/
[cors-docs]: ../topics/ajax-csrf-cors.md
[jsonp-security]: http://stackoverflow.com/questions/613962/is-jsonp-safe-to-use
[testing]: testing.md
[HATEOAS]: http://timelessrepo.com/haters-gonna-hateoas
[quote]: http://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven
[application/vnd.github+json]: http://developer.github.com/v3/media/
[application/vnd.collection+json]: http://www.amundsen.com/media-types/collection/
[django-error-views]: https://docs.djangoproject.com/en/dev/topics/http/views/#customizing-error-views
[messagepack]: http://msgpack.org/
[juanriaza]: https://github.com/juanriaza
[mjumbewu]: https://github.com/mjumbewu
[vbabiy]: https://github.com/vbabiy
[djangorestframework-msgpack]: https://github.com/juanriaza/django-rest-framework-msgpack
[djangorestframework-csv]: https://github.com/mjumbewu/django-rest-framework-csv
[ultrajson]: https://github.com/esnme/ultrajson
[hzy]: https://github.com/hzy
[drf-ujson-renderer]: https://github.com/gizmag/drf-ujson-renderer
[djangorestframework-camel-case]: https://github.com/vbabiy/djangorestframework-camel-case