# Tutorial 6 - ViewSets & Routers

REST framework includes an abstraction for dealing with `ViewSets`, that allows the developer to concentrate on modelling the state and interactions of the API, and leave the URL construction to be handled automatically, based on common conventions.

`ViewSet` classes are almost the same thing as `View` classes, except that they provide operations such as `read`, or `update`, and not method handlers such as `get` or `put`.

A `ViewSet` class is only bound to a set of method handlers at the last moment, when it is instantiated into a set of views, typically by using a `Router` class which handles the complexities of defining the URL conf for you.

## Refactoring to use ViewSets

Let's take our current set of views, and refactor them into view sets.

First of all let's refactor our `UserListView` and `UserDetailView` views into a single `UserViewSet`.  We can remove the two views, and replace then with a single class:

    class UserViewSet(viewsets.ReadOnlyModelViewSet):
        """
        This viewset automatically provides `list` and `detail` actions.
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer

Here we've used `ReadOnlyModelViewSet` class to automatically provide the default 'read-only' operations.  We're still setting the `queryset` and `serializer_class` attributes exactly as we did when we were using regular views, but we no longer need to provide the same information to two seperate classes.

Next we're going to replace the `SnippetList`, `SnippetDetail` and `SnippetHighlight` view classes.  We can remove the three views, and again replace them with a single class.

    from rest_framework import viewsets
    from rest_framework.decorators import link

    class SnippetViewSet(viewsets.ModelViewSet):
        """
        This viewset automatically provides `list`, `create`, `retrieve`,
        `update` and `destroy` actions.
        
        Additionally we also provide an extra `highlight` action. 
        """
        queryset = Snippet.objects.all()
        serializer_class = SnippetSerializer
        permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                              IsOwnerOrReadOnly,)

        @link(renderer_classes=[renderers.StaticHTMLRenderer])
        def highlight(self, request, *args, **kwargs):
            snippet = self.get_object()
            return Response(snippet.highlighted)

        def pre_save(self, obj):
            obj.owner = self.request.user

This time we've used the `ModelViewSet` class in order to get the complete set of default read and write operations.

Notice that we've also used the `@link` decorator to create a custom action, named `highlight`.  This decorator can be used to add any custom endpoints that don't fit into the standard `create`/`update`/`delete` style.

Custom actions which use the `@link` decorator will respond to `GET` requests.  We could have instead used the `@action` decorator if we wanted an action that responded to `POST` requests.

## Binding ViewSets to URLs explicitly

The handler methods only get bound to the actions when we define the URLConf.
To see what's going on under the hood let's first explicitly create a set of views from our ViewSets.

In the `urls.py` file we bind our `ViewSet` classes into a set of concrete views.

    from snippets.resources import SnippetResource, UserResource

    snippet_list = SnippetViewSet.as_view({
        'get': 'list',
        'post': 'create'
    })
    snippet_detail = SnippetViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy'
    })
    snippet_highlight = SnippetViewSet.as_view({
        'get': 'highlight'
    })
    user_list = UserViewSet.as_view({
        'get': 'list'
    })
    user_detail = UserViewSet.as_view({
        'get': 'retrieve'
    })

Notice how we're creating multiple views from each `ViewSet` class, by binding the http methods to the required action for each view.

Now that we've bound our resources into concrete views, that we can register the views with the URL conf as usual.

    urlpatterns = format_suffix_patterns(patterns('snippets.views',
        url(r'^$', 'api_root'),
        url(r'^snippets/$', snippet_list, name='snippet-list'),
        url(r'^snippets/(?P<pk>[0-9]+)/$', snippet_detail, name='snippet-detail'),
        url(r'^snippets/(?P<pk>[0-9]+)/highlight/$', snippet_highlight, name='snippet-highlight'),
        url(r'^users/$', user_list, name='user-list'),
        url(r'^users/(?P<pk>[0-9]+)/$', user_detail, name='user-detail')
    ))

## Using Routers

Because we're using `ViewSet` classes rather than `View` classes, we actually don't need to design the URL conf ourselves.  The conventions for wiring up resources into views and urls can be handled automatically, using a `Router` class.  All we need to do is register the appropriate view sets with a router, and let it do the rest.

Here's our re-wired `urls.py` file.

    from snippets import views
    from rest_framework.routers import DefaultRouter

    # Create a router and register our views and view sets with it.
    router = DefaultRouter()
    router.register(r'^/$', views.api_root)
    router.register(r'^snippets/', views.SnippetViewSet, 'snippet')
    router.register(r'^users/', views.UserViewSet, 'user')
    
    # The urlconf is determined automatically by the router.
    urlpatterns = router.urlpatterns
    
    # We can still add format suffixes to all our URL patterns.
    urlpatterns = format_suffix_patterns(urlpatterns)

## Trade-offs between views vs viewsets.

Using view sets can be a really useful abstraction.  It helps ensure that URL conventions will be consistent across your API, minimises the amount of code you need to write, and allows you to concentrate on the interactions and representations your API provides rather than the specifics of the URL conf.

That doesn't mean it's always the right approach to take.  There's a similar set of trade-offs to consider as when using class-based views instead of function based views.  Using view sets is less explicit than building your views individually.

