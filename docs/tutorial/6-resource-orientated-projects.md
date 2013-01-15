# Tutorial 6 - Resources

REST framework includes an abstraction for dealing with resources, that allows the developer to concentrate on modelling the state and interactions of the API, and leave the URL construction to be handled automatically, based on common conventions.

To work with resources, we can use either the `Resource` class, which does not define any default handlers, or the `ModelResource` class, which provides a default set of CRUD operations.

Resource classes are very similar to class based views, except that they provide operations such as `read`, or `update`, and not HTTP method handlers such as `get` or `put`.  Resources are only bound to HTTP method handlers at the last moment, when they are instantiated into views, typically by using a `Router` class which handles the complexities of defining the URL conf for you.

## Refactoring to use Resources, instead of Views

Let's take our current set of views, and refactor them into resources.
We'll remove our existing `views.py` module, and instead create a `resources.py`

Our `UserResource` is simple, since we just want the default model CRUD behavior, so we inherit from `ModelResource` and include the same set of attributes we used for the corresponding view classes.

    class UserResource(resources.ModelResource):
        model = User
        serializer_class = UserSerializer

There's a little bit more work to do for the `SnippetResource`.  Again, we want the 
default set of CRUD behavior, but we also want to include an endpoint for snippet highlights. 

    class SnippetResource(resources.ModelResource):
        model = Snippet
        serializer_class = SnippetSerializer
        permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                              IsOwnerOrReadOnly,)

        @link(renderer_classes=[renderers.StaticHTMLRenderer])
        def highlight(self, request, *args, **kwargs):
            snippet = self.get_object()
            return Response(snippet.highlighted)

        def pre_save(self, obj):
            obj.owner = self.request.user

Notice that we've used the `@link` decorator for the `highlight` endpoint.  This decorator can be used for non-CRUD endpoints that are "safe" operations that do not change server state.  Using `@link` indicates that we want to use a `GET` method for these operations.  For non-CRUD operations we can also use the `@action` decorator for any operations that change server state, which ensures that the `POST` method will be used for the operation.


## Binding Resources to URLs explicitly

The handler methods only get bound to the actions when we define the URLConf.
To see what's going on under the hood let's first explicitly create a set of views from our resources.

In the `urls.py` file we first need to bind our resources to concrete views.

    snippet_list = SnippetResource.as_view(actions={
        'get': 'list',
        'post': 'create'
    })
    snippet_detail = SnippetResource.as_view(actions={
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })
    snippet_highlight = SnippetResource.as_view(actions={
        'get': 'highlight'
    })
    user_list = UserResource.as_view(actions={
        'get': 'list',
        'post': 'create'
    })
    user_detail = UserResource.as_view(actions={
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })

We've now got a set of views exactly as we did before, that we can register with the URL conf.

Replace the remainder of the `urls.py` file with the following:

    urlpatterns = format_suffix_patterns(patterns('snippets.views',
        url(r'^$', 'api_root'),
        url(r'^snippets/$',
            snippet_list,
            name='snippet-list'),
        url(r'^snippets/(?P<pk>[0-9]+)/$',
            snippet_detail,
            name='snippet-detail'),
        url(r'^snippets/(?P<pk>[0-9]+)/highlight/$',
            snippet_highlight,
            name='snippet-highlight'),
        url(r'^users/$',
            user_list,
            name='user-list'),
        url(r'^users/(?P<pk>[0-9]+)/$',
            user_detail,
            name='user-detail')
    ))

## Using Routers

Right now that hasn't really saved us a lot of code.  However, now that we're using Resources rather than Views, we actually don't need to design the urlconf ourselves.  The conventions for wiring up resources into views and urls can be handled automatically, using `Router` classes.  All we need to do is register the appropriate resources with a router, and let it do the rest.  Here's our re-wired `urls.py` file.

    from blog import resources
    from rest_framework.routers import DefaultRouter

    router = DefaultRouter(include_root=True, include_format_suffixes=True)
    router.register(resources.SnippetResource)
    router.register(resources.UserResource)
    urlpatterns = router.urlpatterns

## Trade-offs between views vs resources.

Writing resource-oriented code can be a good thing.  It helps ensure that URL conventions will be consistent across your APIs, minimises the amount of code you need to write, and allows you to concentrate on the interactions and representations your API provides rather than the specifics of the URL conf.

That doesn't mean it's always the right approach to take.  There's a similar set of trade-offs to consider as when using class-based views.  Using resources is less explicit than building your views individually.

