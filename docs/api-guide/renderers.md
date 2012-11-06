<a class="github" href="renderers.py"></a>

# Renderers

> Before a TemplateResponse instance can be returned to the client, it must be rendered. The rendering process takes the intermediate representation of template and context, and turns it into the final byte stream that can be served to the client.
>
> &mdash; [Django documentation][cite]

REST framework includes a number of built in Renderer classes, that allow you to return responses with various media types.  There is also support for defining your own custom renderers, which gives you the flexibility to design your own media types.

## How the renderer is determined

The set of valid renderers for a view is always defined as a list of classes.  When a view is entered REST framework will perform content negotiation on the incoming request, and determine the most appropriate renderer to satisfy the request.

The basic process of content negotiation involves examining the request's `Accept` header, to determine which media types it expects in the response.  Optionally, format suffixes on the URL may be used to explicitly request a particular representation.  For example the URL `http://example.com/api/users_count.json` might be an endpoint that always returns JSON data.

For more information see the documentation on [content negotation][conneg].

## Setting the renderers

The default set of renderers may be set globally, using the `DEFAULT_RENDERER_CLASSES` setting.  For example, the following settings would use `YAML` as the main media type and also include the self describing API.

    REST_FRAMEWORK = {
        'DEFAULT_RENDERER_CLASSES': (
            'rest_framework.renderers.YAMLRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        )
    }

You can also set the renderers used for an individual view, using the `APIView` class based views.

    class UserCountView(APIView):
        """
        A view that returns the count of active users, in JSON or JSONp.
        """
        renderer_classes = (JSONRenderer, JSONPRenderer)

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

For example if your API serves JSON responses and the HTML browseable API, you might want to make `JSONRenderer` your default renderer, in order to send `JSON` responses to clients that do not specify an `Accept` header.

If your API includes views that can serve both regular webpages and API responses depending on the request, then you might consider making `TemplateHTMLRenderer` your default renderer, in order to play nicely with older browsers that send [broken accept headers][browser-accept-headers].

---

# API Reference

## JSONRenderer

Renders the request data into `JSON`.

The client may additionally include an `'indent'` media type parameter, in which case the returned `JSON` will be indented.  For example `Accept: application/json; indent=4`.

**.media_type**: `application/json`

**.format**: `'.json'`

## JSONPRenderer

Renders the request data into `JSONP`.  The `JSONP` media type provides a mechanism of allowing cross-domain AJAX requests, by wrapping a `JSON` response in a javascript callback.

The javascript callback function must be set by the client including a `callback` URL query parameter.  For example `http://example.com/api/users?callback=jsonpCallback`.  If the callback function is not explicitly set by the client it will default to `'callback'`.

**Note**: If you require cross-domain AJAX requests, you may also want to consider using [CORS] as an alternative to `JSONP`.

**.media_type**: `application/javascript`

**.format**: `'.jsonp'`

## YAMLRenderer

Renders the request data into `YAML`. 

**.media_type**: `application/yaml`

**.format**: `'.yaml'`

## XMLRenderer

Renders REST framework's default style of `XML` response content.

Note that the `XML` markup language is used typically used as the base language for more strictly defined domain-specific languages, such as `RSS`, `Atom`, and `XHTML`.

If you are considering using `XML` for your API, you may want to consider implementing a custom renderer and parser for your specific requirements, and using an existing domain-specific media-type, or creating your own custom XML-based media-type.

**.media_type**: `application/xml`

**.format**: `'.xml'`

## TemplateHTMLRenderer

Renders data to HTML, using Django's standard template rendering.
Unlike other renderers, the data passed to the `Response` does not need to be serialized.  Also, unlike other renderers, you may want to include a `template_name` argument when creating the `Response`.

The TemplateHTMLRenderer will create a `RequestContext`, using the `response.data` as the context dict, and determine a template name to use to render the context.

The template name is determined by (in order of preference):

1. An explicit `.template_name` attribute set on the response.
2. An explicit `.template_name` attribute set on this class.
3. The return result of calling `view.get_template_names()`.

An example of a view that uses `TemplateHTMLRenderer`:

    class UserInstance(generics.RetrieveUserAPIView):
        """
        A view that returns a templated HTML representations of a given user.
        """
        model = Users
        renderer_classes = (TemplateHTMLRenderer,)

        def get(self, request, *args, **kwargs)
            self.object = self.get_object()
            return Response({'user': self.object}, template_name='user_detail.html')
 
You can use `TemplateHTMLRenderer` either to return regular HTML pages using REST framework, or to return both HTML and API responses from a single endpoint.

If you're building websites that use `TemplateHTMLRenderer` along with other renderer classes, you should consider listing `TemplateHTMLRenderer` as the first class in the `renderer_classes` list, so that it will be prioritised first even for browsers that send poorly formed `ACCEPT:` headers.

**.media_type**: `text/html`

**.format**: `'.html'`

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

See also: `TemplateHTMLRenderer`

## BrowsableAPIRenderer

Renders data into HTML for the Browseable API.  This renderer will determine which other renderer would have been given highest priority, and use that to display an API style response within the HTML page.

**.media_type**: `text/html`

**.format**: `'.api'`

---

# Custom renderers

To implement a custom renderer, you should override `BaseRenderer`, set the `.media_type` and `.format` properties, and implement the `.render(self, data, media_type=None, renderer_context=None)` method.

The arguments passed to the `.render()` method are:

### `data`

The request data, as set by the `Response()` instantiation.

### `media_type=None`

Optional. If provided, this is the accepted media type, as determined by the content negotiation stage.

Depending on the client's `Accept:` header, this may be more specific than the renderer's `media_type` attribute, and may include media type parameters.  For example `"application/json; nested=true"`.

### `renderer_context=None`

Optional. If provided, this is a dictionary of contextual information provided by the view.

By default this will include the following keys: `view`, `request`, `response`, `args`, `kwargs`.

## Example

The following is an example plaintext renderer that will return a response with the `data` parameter as the content of the response.

    from django.utils.encoding import smart_unicode
    from rest_framework import renderers


    class PlainText(renderers.BaseRenderer):
        media_type = 'text/plain'
        format = 'txt'
        
        def render(self, data, media_type=None, renderer_context=None):
            if isinstance(data, basestring):
                return data
            return smart_unicode(data)

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


[cite]: https://docs.djangoproject.com/en/dev/ref/template-response/#the-rendering-process
[conneg]: content-negotiation.md
[browser-accept-headers]: http://www.gethifi.com/blog/browser-rest-http-accept-headers
[CORS]: http://en.wikipedia.org/wiki/Cross-origin_resource_sharing
[HATEOAS]: http://timelessrepo.com/haters-gonna-hateoas
[quote]: http://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven
[application/vnd.github+json]: http://developer.github.com/v3/media/
[application/vnd.collection+json]: http://www.amundsen.com/media-types/collection/
[django-error-views]: https://docs.djangoproject.com/en/dev/topics/http/views/#customizing-error-views