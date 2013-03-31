<a class="github" href="routers.py"></a> <a class="github" href="viewsets.py"></a>

# ViewSets & Routers

> Resource routing allows you to quickly declare all of the common routes for a given resourceful controller. Instead of declaring separate routes for your index... a resourceful route declares them in a single line of code.
>
> &mdash; [Ruby on Rails Documentation][cite]

Some Web frameworks such as Rails provide functionality for automatically determining how the URLs for an application should be mapped to the logic that deals with handling incoming requests.

Conversely, Django stops short of automatically generating URLs, and requires you to explicitly manage your URL configuration.

REST framework adds support for automatic URL routing, which provides you with a simple, quick and consistent way of wiring your view logic to a set of URLs.

# ViewSets

Django REST framework allows you to combine the logic for a set of related views in a single class, called a `ViewSet`.  In other frameworks you may also find conceptually similar implementations named something like 'Resources' or 'Controllers'.

A `ViewSet` class is simply **a type of class-based View, that does not provide any method handlers** such as `.get()` or `.post()`, and instead provides actions such as `.list()` and `.create()`.

The method handlers for a `ViewSet` are only bound to the corresponding actions at the point of finalizing the view, using the `.as_view()` method.

Typically, rather than exlicitly registering the views in a viewset in the urlconf, you'll register the viewset with a router class, that automatically determines the urlconf for you.

## Example

Let's define a simple viewset that can be used to listing or retrieving all the users in the system.

    class UserViewSet(ViewSet):
        """
        A simple ViewSet that for listing or retrieving users.
        """
        queryset = User.objects.all()

        def list(self, request):
            serializer = UserSerializer(self.queryset, many=True)
            return Response(serializer.data)
            
        def retrieve(self, request, pk=None):
            user = get_object_or_404(self.queryset, pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)

If we need to, we can bind this viewset into two seperate views, like so:

    user_list = UserViewSet.as_view({'get': 'list'})
    user_detail = UserViewSet.as_view({'get': 'retrieve'})

Typically we wouldn't do this, but would instead register the viewset with a router, and allow the urlconf to be automatically generated.

# API Reference

## ViewSet

The `ViewSet` class inherits from `APIView`.  You can use any of the standard attributes such as `permission_classes`, `authentication_classes` in order to control the API policy on the viewset.

The `ViewSet` class does not provide any implementations of actions.  In order to use a `ViewSet` class you'll override the class and define the action implementations explicitly.

## ModelViewSet

The `ModelViewSet` class inherits from `GenericAPIView` and includes implementations for various actions, by mixing in the behavior of the

The actions provided by the `ModelViewSet` class are `.list()`, `.retrieve()`,  `.create()`, `.update()`, and `.destroy()`.

## ReadOnlyModelViewSet

The `ReadOnlyModelViewSet` class also inherits from `GenericAPIView`.  As with `ModelViewSet` it also includes implementations for various actions, but unlike `ModelViewSet` only provides the 'read-only' actions, `.list()` and `.retrieve()`.

# Custom ViewSet base classes 

Any standard `View` class can be turned into a `ViewSet` class by mixing in `ViewSetMixin`.  You can use this to define your own base classes.

For example, the definition of `ModelViewSet` looks like this:

    class ModelViewSet(mixins.CreateModelMixin,
                       mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       mixins.DestroyModelMixin,
                       mixins.ListModelMixin,
                       viewsets.ViewSetMixin,
                       generics.GenericAPIView):
        """
        A viewset that provides actions for `create`, `retrieve`,
        `update`, `destroy` and `list` actions.
        
        To use it, override the class and set the `.queryset`
        and `.serializer_class` attributes.
        """
        pass

By creating your own base `ViewSet` classes, you can provide common behavior that can be reused in multiple views across your API.

Note the that `ViewSetMixin` class can also be applied to the standard Django `View` class if you want to use REST framework's automatic routing, but don't want to use it's permissions, authentication and other API policies.

---

# Routers

Routers provide a convenient and simple shortcut for wiring up your application's URLs.

    router = routers.DefaultRouter()
    router.register('^/', APIRoot, 'api-root')
    router.register('^users/', UserViewSet, 'user')
    router.register('^groups/', GroupViewSet, 'group')
    router.register('^accounts/', AccountViewSet, 'account')

    urlpatterns = router.urlpatterns

[cite]: http://guides.rubyonrails.org/routing.html