# Tutorial 6: ViewSets & Routers

REST framework includes an abstraction for dealing with `ViewSets`, that allows the developer to concentrate on modeling the state and interactions of the API, and leave the URL construction to be handled automatically, based on common conventions.

`ViewSet` classes are almost the same thing as `View` classes, except that they provide operations such as `read`, or `update`, and not method handlers such as `get` or `put`.

A `ViewSet` class is only bound to a set of method handlers at the last moment, when it is instantiated into a set of views, typically by using a `Router` class which handles the complexities of defining the URL conf for you.

## Refactoring to use ViewSets

Let's take our current set of views, and refactor them into view sets.

First of all let's refactor our `UserList` and `UserDetail` views into a single `UserViewSet`.  We can remove the two views, and replace them with a single class:

    from rest_framework import viewsets

    class UserViewSet(viewsets.ReadOnlyModelViewSet):
        """
        This viewset automatically provides `list` and `detail` actions.
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer

Here we've used `ReadOnlyModelViewSet` class to automatically provide the default 'read-only' operations.  We're still setting the `queryset` and `serializer_class` attributes exactly as we did when we were using regular views, but we no longer need to provide the same information to two separate classes.

Next we're going to replace the `SnippetList`, `SnippetDetail` and `SnippetHighlight` view classes.  We can remove the three views, and again replace them with a single class.

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

    from snippets.views import SnippetViewSet, UserViewSet
    from rest_framework import renderers

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
    }, renderer_classes=[renderers.StaticHTMLRenderer])
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

    from django.conf.urls import patterns, url, include
    from snippets import views
    from rest_framework.routers import DefaultRouter

    # Create a router and register our viewsets with it.
    router = DefaultRouter()
    router.register(r'snippets', views.SnippetViewSet)
    router.register(r'users', views.UserViewSet)

    # The API URLs are now determined automatically by the router.
    # Additionally, we include the login URLs for the browseable API.
    urlpatterns = patterns('',
        url(r'^', include(router.urls)),
        url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    )

Registering the viewsets with the router is similar to providing a urlpattern.  We include two arguments - the URL prefix for the views, and the viewset itself.

The `DefaultRouter` class we're using also automatically creates the API root view for us, so we can now delete the `api_root` method from our `views` module.

## Trade-offs between views vs viewsets

Using viewsets can be a really useful abstraction.  It helps ensure that URL conventions will be consistent across your API, minimizes the amount of code you need to write, and allows you to concentrate on the interactions and representations your API provides rather than the specifics of the URL conf.

That doesn't mean it's always the right approach to take.  There's a similar set of trade-offs to consider as when using class-based views instead of function based views.  Using viewsets is less explicit than building your views individually.

## Reviewing our work

With an incredibly small amount of code, we've now got a complete pastebin Web API, which is fully web browseable, and comes complete with authentication, per-object permissions, and multiple renderer formats.

We've walked through each step of the design process, and seen how if we need to customize anything we can gradually work our way down to simply using regular Django views.

You can review the final [tutorial code][repo] on GitHub, or try out a live example in [the sandbox][sandbox].

## Onwards and upwards

We've reached the end of our tutorial.  If you want to get more involved in the REST framework project, here's a few places you can start:

* Contribute on [GitHub][github] by reviewing and submitting issues, and making pull requests.
* Join the [REST framework discussion group][group], and help build the community.
* Follow [the author][twitter] on Twitter and say hi.

**Now go build awesome things.**


[repo]: https://github.com/tomchristie/rest-framework-tutorial
[sandbox]: http://restframework.herokuapp.com/
[github]: https://github.com/tomchristie/django-rest-framework
[group]: https://groups.google.com/forum/?fromgroups#!forum/django-rest-framework
[twitter]: https://twitter.com/_tomchristie
