source: routers.py

# Routers

> Resource routing allows you to quickly declare all of the common routes for a given resourceful controller.  Instead of declaring separate routes for your index... a resourceful route declares them in a single line of code.
>
> &mdash; [Ruby on Rails Documentation][cite]

Some Web frameworks such as Rails provide functionality for automatically determining how the URLs for an application should be mapped to the logic that deals with handling incoming requests.

REST framework adds support for automatic URL routing to Django, and provides you with a simple, quick and consistent way of wiring your view logic to a set of URLs.

## Usage

Here's an example of a simple URL conf, that uses `SimpleRouter`.

    from rest_framework import routers

    router = routers.SimpleRouter()
    router.register(r'users', UserViewSet)
    router.register(r'accounts', AccountViewSet)
    urlpatterns = router.urls

There are two mandatory arguments to the `register()` method:

* `prefix` - The URL prefix to use for this set of routes.
* `viewset` - The viewset class.

Optionally, you may also specify an additional argument:

* `base_name` - The base to use for the URL names that are created.  If unset the basename will be automatically generated based on the `queryset` attribute of the viewset, if it has one.  Note that if the viewset does not include a `queryset` attribute then you must set `base_name` when registering the viewset.

The example above would generate the following URL patterns:

* URL pattern: `^users/$`  Name: `'user-list'`
* URL pattern: `^users/{pk}/$`  Name: `'user-detail'`
* URL pattern: `^accounts/$`  Name: `'account-list'`
* URL pattern: `^accounts/{pk}/$`  Name: `'account-detail'`

---

**Note**: The `base_name` argument is used to specify the initial part of the view name pattern.  In the example above, that's the `user` or `account` part.

Typically you won't *need* to specify the `base_name` argument, but if you have a viewset where you've defined a custom `get_queryset` method, then the viewset may not have a `.queryset` attribute set.  If you try to register that viewset you'll see an error like this:

    'base_name' argument not specified, and could not automatically determine the name from the viewset, as it does not have a '.queryset' attribute.

This means you'll need to explicitly set the `base_name` argument when registering the viewset, as it could not be automatically determined from the model name.

---

### Using `include` with routers

The `.urls` attribute on a router instance is simply a standard list of URL patterns. There are a number of different styles for how you can include these URLs.

For example, you can append `router.urls` to a list of existing views…

    router = routers.SimpleRouter()
    router.register(r'users', UserViewSet)
    router.register(r'accounts', AccountViewSet)
    
    urlpatterns = [
        url(r'^forgot-password/$', ForgotPasswordFormView.as_view()),
    ]
    
    urlpatterns += router.urls

Alternatively you can use Django's `include` function, like so…

    urlpatterns = [
        url(r'^forgot-password/$', ForgotPasswordFormView.as_view()),
        url(r'^', include(router.urls)),
    ]

Router URL patterns can also be namespaces.

    urlpatterns = [
        url(r'^forgot-password/$', ForgotPasswordFormView.as_view()),
        url(r'^api/', include(router.urls, namespace='api')),
    ]

If using namespacing with hyperlinked serializers you'll also need to ensure that any `view_name` parameters on the serializers correctly reflect the namespace. In the example above you'd need to include a parameter such as `view_name='api:user-detail'` for serializer fields hyperlinked to the user detail view.

### Extra link and actions

Any methods on the viewset decorated with `@detail_route` or `@list_route` will also be routed.
For example, given a method like this on the `UserViewSet` class:

    from myapp.permissions import IsAdminOrIsSelf
    from rest_framework.decorators import detail_route

    class UserViewSet(ModelViewSet):
        ...

        @detail_route(methods=['post'], permission_classes=[IsAdminOrIsSelf])
        def set_password(self, request, pk=None):
            ...

The following URL pattern would additionally be generated:

* URL pattern: `^users/{pk}/set_password/$`  Name: `'user-set-password'`

If you do not want to use the default URL generated for your custom action, you can instead use the url_path parameter to customize it.

For example, if you want to change the URL for our custom action to `^users/{pk}/change-password/$`, you could write:

    from myapp.permissions import IsAdminOrIsSelf
    from rest_framework.decorators import detail_route
    
    class UserViewSet(ModelViewSet):
        ...
        
        @detail_route(methods=['post'], permission_classes=[IsAdminOrIsSelf], url_path='change-password')
        def set_password(self, request, pk=None):
            ...

The above example would now generate the following URL pattern:

* URL pattern: `^users/{pk}/change-password/$`  Name: `'user-change-password'`

In the case you do not want to use the default name generated for your custom action, you can use the url_name parameter to customize it.

For example, if you want to change the name of our custom action to `'user-change-password'`, you could write:

    from myapp.permissions import IsAdminOrIsSelf
    from rest_framework.decorators import detail_route
    
    class UserViewSet(ModelViewSet):
        ...
        
        @detail_route(methods=['post'], permission_classes=[IsAdminOrIsSelf], url_name='change-password')
        def set_password(self, request, pk=None):
            ...

The above example would now generate the following URL pattern:

* URL pattern: `^users/{pk}/set_password/$`  Name: `'user-change-password'`

You can also use url_path and url_name parameters together to obtain extra control on URL generation for custom views.

For more information see the viewset documentation on [marking extra actions for routing][route-decorators].

# API Guide

## SimpleRouter

This router includes routes for the standard set of `list`, `create`, `retrieve`, `update`, `partial_update` and `destroy` actions.  The viewset can also mark additional methods to be routed, using the `@detail_route` or `@list_route` decorators.

<table border=1>
    <tr><th>URL Style</th><th>HTTP Method</th><th>Action</th><th>URL Name</th></tr>
    <tr><td rowspan=2>{prefix}/</td><td>GET</td><td>list</td><td rowspan=2>{basename}-list</td></tr></tr>
    <tr><td>POST</td><td>create</td></tr>
    <tr><td>{prefix}/{methodname}/</td><td>GET, or as specified by `methods` argument</td><td>`@list_route` decorated method</td><td>{basename}-{methodname}</td></tr>
    <tr><td rowspan=4>{prefix}/{lookup}/</td><td>GET</td><td>retrieve</td><td rowspan=4>{basename}-detail</td></tr></tr>
    <tr><td>PUT</td><td>update</td></tr>
    <tr><td>PATCH</td><td>partial_update</td></tr>
    <tr><td>DELETE</td><td>destroy</td></tr>
    <tr><td>{prefix}/{lookup}/{methodname}/</td><td>GET, or as specified by `methods` argument</td><td>`@detail_route` decorated method</td><td>{basename}-{methodname}</td></tr>
</table>

By default the URLs created by `SimpleRouter` are appended with a trailing slash.
This behavior can be modified by setting the `trailing_slash` argument to `False` when instantiating the router.  For example:

    router = SimpleRouter(trailing_slash=False)

Trailing slashes are conventional in Django, but are not used by default in some other frameworks such as Rails.  Which style you choose to use is largely a matter of preference, although some javascript frameworks may expect a particular routing style.

The router will match lookup values containing any characters except slashes and period characters.  For a more restrictive (or lenient) lookup pattern, set the `lookup_value_regex` attribute on the viewset.  For example, you can limit the lookup to valid UUIDs:

    class MyModelViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
        lookup_field = 'my_model_id'
        lookup_value_regex = '[0-9a-f]{32}'

## DefaultRouter

This router is similar to `SimpleRouter` as above, but additionally includes a default API root view, that returns a response containing hyperlinks to all the list views.  It also generates routes for optional `.json` style format suffixes.

<table border=1>
    <tr><th>URL Style</th><th>HTTP Method</th><th>Action</th><th>URL Name</th></tr>
    <tr><td>[.format]</td><td>GET</td><td>automatically generated root view</td><td>api-root</td></tr></tr>
    <tr><td rowspan=2>{prefix}/[.format]</td><td>GET</td><td>list</td><td rowspan=2>{basename}-list</td></tr></tr>
    <tr><td>POST</td><td>create</td></tr>
    <tr><td>{prefix}/{methodname}/[.format]</td><td>GET, or as specified by `methods` argument</td><td>`@list_route` decorated method</td><td>{basename}-{methodname}</td></tr>
    <tr><td rowspan=4>{prefix}/{lookup}/[.format]</td><td>GET</td><td>retrieve</td><td rowspan=4>{basename}-detail</td></tr></tr>
    <tr><td>PUT</td><td>update</td></tr>
    <tr><td>PATCH</td><td>partial_update</td></tr>
    <tr><td>DELETE</td><td>destroy</td></tr>
    <tr><td>{prefix}/{lookup}/{methodname}/[.format]</td><td>GET, or as specified by `methods` argument</td><td>`@detail_route` decorated method</td><td>{basename}-{methodname}</td></tr>
</table>

As with `SimpleRouter` the trailing slashes on the URL routes can be removed by setting the `trailing_slash` argument to `False` when instantiating the router.

    router = DefaultRouter(trailing_slash=False)

# Custom Routers

Implementing a custom router isn't something you'd need to do very often, but it can be useful if you have specific requirements about how the your URLs for your API are structured.  Doing so allows you to encapsulate the URL structure in a reusable way that ensures you don't have to write your URL patterns explicitly for each new view.

The simplest way to implement a custom router is to subclass one of the existing router classes.  The `.routes` attribute is used to template the URL patterns that will be mapped to each viewset. The `.routes` attribute is a list of `Route` named tuples.

The arguments to the `Route` named tuple are:

**url**: A string representing the URL to be routed.  May include the following format strings:

* `{prefix}` - The URL prefix to use for this set of routes.
* `{lookup}` - The lookup field used to match against a single instance.
* `{trailing_slash}` - Either a '/' or an empty string, depending on the `trailing_slash` argument.

**mapping**: A mapping of HTTP method names to the view methods

**name**: The name of the URL as used in `reverse` calls. May include the following format string:

* `{basename}` - The base to use for the URL names that are created.

**initkwargs**: A dictionary of any additional arguments that should be passed when instantiating the view.  Note that the `suffix` argument is reserved for identifying the viewset type, used when generating the view name and breadcrumb links.

## Customizing dynamic routes

You can also customize how the `@list_route` and `@detail_route` decorators are routed.
To route either or both of these decorators, include a `DynamicListRoute` and/or `DynamicDetailRoute` named tuple in the `.routes` list.

The arguments to `DynamicListRoute` and `DynamicDetailRoute` are:

**url**: A string representing the URL to be routed. May include the same format strings as `Route`, and additionally accepts the `{methodname}` and `{methodnamehyphen}` format strings.

**name**: The name of the URL as used in `reverse` calls. May include the following format strings: `{basename}`, `{methodname}` and `{methodnamehyphen}`.

**initkwargs**: A dictionary of any additional arguments that should be passed when instantiating the view.

## Example

The following example will only route to the `list` and `retrieve` actions, and does not use the trailing slash convention.

    from rest_framework.routers import Route, DynamicDetailRoute, SimpleRouter

    class CustomReadOnlyRouter(SimpleRouter):
        """
        A router for read-only APIs, which doesn't use trailing slashes.
        """
        routes = [
            Route(
            	url=r'^{prefix}$',
            	mapping={'get': 'list'},
            	name='{basename}-list',
            	initkwargs={'suffix': 'List'}
            ),
            Route(
            	url=r'^{prefix}/{lookup}$',
                mapping={'get': 'retrieve'},
                name='{basename}-detail',
                initkwargs={'suffix': 'Detail'}
            ),
            DynamicDetailRoute(
            	url=r'^{prefix}/{lookup}/{methodnamehyphen}$',
            	name='{basename}-{methodnamehyphen}',
            	initkwargs={}
        	)
        ]

Let's take a look at the routes our `CustomReadOnlyRouter` would generate for a simple viewset.

`views.py`:

    class UserViewSet(viewsets.ReadOnlyModelViewSet):
        """
        A viewset that provides the standard actions
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer
        lookup_field = 'username'

        @detail_route()
        def group_names(self, request):
            """
            Returns a list of all the group names that the given
            user belongs to.
            """
            user = self.get_object()
            groups = user.groups.all()
            return Response([group.name for group in groups])

`urls.py`:

    router = CustomReadOnlyRouter()
    router.register('users', UserViewSet)
	urlpatterns = router.urls

The following mappings would be generated...

<table border=1>
    <tr><th>URL</th><th>HTTP Method</th><th>Action</th><th>URL Name</th></tr>
    <tr><td>/users</td><td>GET</td><td>list</td><td>user-list</td></tr>
    <tr><td>/users/{username}</td><td>GET</td><td>retrieve</td><td>user-detail</td></tr>
    <tr><td>/users/{username}/group-names</td><td>GET</td><td>group_names</td><td>user-group-names</td></tr>
</table>

For another example of setting the `.routes` attribute, see the source code for the `SimpleRouter` class.

## Advanced custom routers

If you want to provide totally custom behavior, you can override `BaseRouter` and override the `get_urls(self)` method.  The method should inspect the registered viewsets and return a list of URL patterns.  The registered prefix, viewset and basename tuples may be inspected by accessing the `self.registry` attribute.

You may also want to override the `get_default_base_name(self, viewset)` method, or else always explicitly set the `base_name` argument when registering your viewsets with the router.

# Third Party Packages

The following third party packages are also available.

## DRF Nested Routers

The [drf-nested-routers package][drf-nested-routers] provides routers and relationship fields for working with nested resources.

## ModelRouter (wq.db.rest)

The [wq.db package][wq.db] provides an advanced [ModelRouter][wq.db-router] class (and singleton instance) that extends `DefaultRouter` with a `register_model()` API. Much like Django's `admin.site.register`, the only required argument to `rest.router.register_model` is a model class.  Reasonable defaults for a url prefix, serializer, and viewset will be inferred from the model and global configuration.

    from wq.db import rest
    from myapp.models import MyModel

    rest.router.register_model(MyModel)

## DRF-extensions

The [`DRF-extensions` package][drf-extensions] provides [routers][drf-extensions-routers] for creating [nested viewsets][drf-extensions-nested-viewsets], [collection level controllers][drf-extensions-collection-level-controllers] with [customizable endpoint names][drf-extensions-customizable-endpoint-names].

[cite]: http://guides.rubyonrails.org/routing.html
[route-decorators]: viewsets.md#marking-extra-actions-for-routing
[drf-nested-routers]: https://github.com/alanjds/drf-nested-routers
[wq.db]: http://wq.io/wq.db
[wq.db-router]: http://wq.io/docs/router
[drf-extensions]: http://chibisov.github.io/drf-extensions/docs/
[drf-extensions-routers]: http://chibisov.github.io/drf-extensions/docs/#routers
[drf-extensions-nested-viewsets]: http://chibisov.github.io/drf-extensions/docs/#nested-routes
[drf-extensions-collection-level-controllers]: http://chibisov.github.io/drf-extensions/docs/#collection-level-controllers
[drf-extensions-customizable-endpoint-names]: http://chibisov.github.io/drf-extensions/docs/#controller-endpoint-name
