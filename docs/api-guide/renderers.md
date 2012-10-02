<a class="github" href="renderers.py"></a>

# Renderers

> Before a TemplateResponse instance can be returned to the client, it must be rendered. The rendering process takes the intermediate representation of template and context, and turns it into the final byte stream that can be served to the client.
>
> &mdash; [Django documentation][cite]

REST framework includes a number of built in Renderer classes, that allow you to return responses with various media types.  There is also support for defining your own custom renderers, which gives you the flexiblity to design your own media types.

## How the renderer is determined

The set of valid renderers for a view is always defined as a list of classes.  When a view is entered REST framework will perform content negotiation on the incoming request, and determine the most appropriate renderer to satisfy the request.

The basic process of content negotiation involves examining the request's `Accept` header, to determine which media types it expects in the response.  Optionally, format suffixes on the URL may be used to explicitly request a particular representation.  For example the URL `http://example.com/api/users_count.json` might be an endpoint that always returns JSON data.

For more information see the documentation on [content negotation][conneg].

## Setting the renderers

The default set of renderers may be set globally, using the `DEFAULT_RENDERERS` setting.  For example, the following settings would use `YAML` as the main media type and also include the self describing API.

    REST_FRAMEWORK = {
        'DEFAULT_RENDERERS': (
            'rest_framework.renderers.YAMLRenderer',
            'rest_framework.renderers.DocumentingHTMLRenderer',
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

    @api_view('GET'),
    @renderer_classes(JSONRenderer, JSONPRenderer)
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

## JSONRenderer

**.media_type:** `application/json`

**.format:** `'.json'`

## JSONPRenderer

**.media_type:** `application/javascript`

**.format:** `'.jsonp'`

## YAMLRenderer

**.media_type:** `application/yaml`

**.format:** `'.yaml'`

## XMLRenderer

**.media_type:** `application/xml`

**.format:** `'.xml'`

## DocumentingHTMLRenderer

**.media_type:** `text/html`

**.format:** `'.api'`

## TemplateHTMLRenderer

**.media_type:** `text/html`

**.format:** `'.html'`

## Custom renderers

To implement a custom renderer, you should override `BaseRenderer`, set the `.media_type` and `.format` properties, and implement the `.render(self, data, media_type)` method.

## Advanced renderer usage

You can do some pretty flexible things using REST framework's renderers.  Some examples...

* Provide either flat or nested representations from the same endpoint, depending on the requested media type.
* Serve both regular HTML webpages, and JSON based API responses from the same endpoints.
* Specify multiple types of HTML representation for API clients to use.
* Underspecify a renderer's media type, such as using `media_type = 'image/*'`, and use the `Accept` header to vary the encoding of the response. 

In some cases you might want your view to use different serialization styles depending on the accepted media type.  If you need to do this you can access `request.accepted_renderer` to determine the negotiated renderer that will be used for the response.

For example:

    @api_view(('GET',))
    @renderer_classes((TemplateHTMLRenderer, JSONRenderer))
    @template_name('list_users.html')
    def list_users(request):
        """
        A view that can return JSON or HTML representations
        of the users in the system.
        """
        queryset = Users.objects.filter(active=True)

        if request.accepted_renderer.format == 'html':
            # TemplateHTMLRenderer takes a context dict,
            # and does not require serialization.
            data = {'users': queryset}
        else:
            # JSONRenderer requires serialized data as normal.
            serializer = UserSerializer(instance=queryset)
            data = serializer.data

        return Response(data)

## Designing your media types

For the purposes of many Web APIs, simple `JSON` responses with hyperlinked relations may be sufficient.  If you want to fully embrace RESTful design and [HATEOAS] you'll neeed to consider the design and usage of your media types in more detail.

In [the words of Roy Fielding][quote], "A REST API should spend almost all of its descriptive effort in defining the media type(s) used for representing resources and driving application state, or in defining extended relation names and/or hypertext-enabled mark-up for existing standard media types.".

For good examples of custom media types, see GitHub's use of a custom [application/vnd.github+json] media type, and Mike Amundsen's IANA approved [application/vnd.collection+json] JSON-based hypermedia.

[cite]: https://docs.djangoproject.com/en/dev/ref/template-response/#the-rendering-process
[conneg]: content-negotiation.md
[browser-accept-headers]: http://www.gethifi.com/blog/browser-rest-http-accept-headers
[HATEOAS]: http://timelessrepo.com/haters-gonna-hateoas
[quote]: http://roy.gbiv.com/untangled/2008/rest-apis-must-be-hypertext-driven
[application/vnd.github+json]: http://developer.github.com/v3/media/
[application/vnd.collection+json]: http://www.amundsen.com/media-types/collection/