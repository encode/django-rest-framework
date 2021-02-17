---
source:
    - viewsets.py
---

# ViewSets

> After routing has determined which controller to use for a request, your controller is responsible for making sense of the request and producing the appropriate output.
>
> &mdash; [Ruby on Rails Documentation][cite]


Django REST framework allows you to combine the logic for a set of related views in a single class, called a `ViewSet`.  In other frameworks you may also find conceptually similar implementations named something like 'Resources' or 'Controllers'.

A `ViewSet` class is simply **a type of class-based View, that does not provide any method handlers** such as `.get()` or `.post()`, and instead provides actions such as `.list()` and `.create()`.

The method handlers for a `ViewSet` are only bound to the corresponding actions at the point of finalizing the view, using the `.as_view()` method.

Typically, rather than explicitly registering the views in a viewset in the urlconf, you'll register the viewset with a router class, that automatically determines the urlconf for you.

## Example

Let's define a simple viewset that can be used to list or retrieve all the users in the system.

    from django.contrib.auth.models import User
    from django.shortcuts import get_object_or_404
    from myapps.serializers import UserSerializer
    from rest_framework import viewsets
    from rest_framework.response import Response

    class UserViewSet(viewsets.ViewSet):
        """
        A simple ViewSet for listing or retrieving users.
        """
        def list(self, request):
            queryset = User.objects.all()
            serializer = UserSerializer(queryset, many=True)
            return Response(serializer.data)

        def retrieve(self, request, pk=None):
            queryset = User.objects.all()
            user = get_object_or_404(queryset, pk=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)

If we need to, we can bind this viewset into two separate views, like so:

    user_list = UserViewSet.as_view({'get': 'list'})
    user_detail = UserViewSet.as_view({'get': 'retrieve'})

Typically we wouldn't do this, but would instead register the viewset with a router, and allow the urlconf to be automatically generated.

    from myapp.views import UserViewSet
    from rest_framework.routers import DefaultRouter

    router = DefaultRouter()
    router.register(r'users', UserViewSet, basename='user')
    urlpatterns = router.urls

Rather than writing your own viewsets, you'll often want to use the existing base classes that provide a default set of behavior.  For example:

    class UserViewSet(viewsets.ModelViewSet):
        """
        A viewset for viewing and editing user instances.
        """
        serializer_class = UserSerializer
        queryset = User.objects.all()

There are two main advantages of using a `ViewSet` class over using a `View` class.

* Repeated logic can be combined into a single class.  In the above example, we only need to specify the `queryset` once, and it'll be used across multiple views.
* By using routers, we no longer need to deal with wiring up the URL conf ourselves.

Both of these come with a trade-off.  Using regular views and URL confs is more explicit and gives you more control.  ViewSets are helpful if you want to get up and running quickly, or when you have a large API and you want to enforce a consistent URL configuration throughout.


## ViewSet actions

The default routers included with REST framework will provide routes for a standard set of create/retrieve/update/destroy style actions, as shown below:

    class UserViewSet(viewsets.ViewSet):
        """
        Example empty viewset demonstrating the standard
        actions that will be handled by a router class.

        If you're using format suffixes, make sure to also include
        the `format=None` keyword argument for each action.
        """

        def list(self, request):
            pass

        def create(self, request):
            pass

        def retrieve(self, request, pk=None):
            pass

        def update(self, request, pk=None):
            pass

        def partial_update(self, request, pk=None):
            pass

        def destroy(self, request, pk=None):
            pass

## Introspecting ViewSet actions

During dispatch, the following attributes are available on the `ViewSet`.

* `basename` - the base to use for the URL names that are created.
* `action` - the name of the current action (e.g., `list`, `create`).
* `detail` - boolean indicating if the current action is configured for a list or detail view.
* `suffix` - the display suffix for the viewset type - mirrors the `detail` attribute.
* `name` - the display name for the viewset. This argument is mutually exclusive to `suffix`.
* `description` - the display description for the individual view of a viewset.

You may inspect these attributes to adjust behaviour based on the current action. For example, you could restrict permissions to everything except the `list` action similar to this:

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'list':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

## Marking extra actions for routing

If you have ad-hoc methods that should be routable, you can mark them as such with the `@action` decorator. Like regular actions, extra actions may be intended for either a single object, or an entire collection. To indicate this, set the `detail` argument to `True` or `False`. The router will configure its URL patterns accordingly. e.g., the `DefaultRouter` will configure detail actions to contain `pk` in their URL patterns.

A more complete example of extra actions:

    from django.contrib.auth.models import User
    from rest_framework import status, viewsets
    from rest_framework.decorators import action
    from rest_framework.response import Response
    from myapp.serializers import UserSerializer, PasswordSerializer

    class UserViewSet(viewsets.ModelViewSet):
        """
        A viewset that provides the standard actions
        """
        queryset = User.objects.all()
        serializer_class = UserSerializer

        @action(detail=True, methods=['post'])
        def set_password(self, request, pk=None):
            user = self.get_object()
            serializer = PasswordSerializer(data=request.data)
            if serializer.is_valid():
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response({'status': 'password set'})
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)

        @action(detail=False)
        def recent_users(self, request):
            recent_users = User.objects.all().order_by('-last_login')

            page = self.paginate_queryset(recent_users)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(recent_users, many=True)
            return Response(serializer.data)


The `action` decorator will route `GET` requests by default, but may also accept other HTTP methods by setting the `methods` argument.  For example:

        @action(detail=True, methods=['post', 'delete'])
        def unset_password(self, request, pk=None):
           ...


The decorator allows you to override any viewset-level configuration such as `permission_classes`, `serializer_class`, `filter_backends`...:

        @action(detail=True, methods=['post'], permission_classes=[IsAdminOrIsSelf])
        def set_password(self, request, pk=None):
           ...

The two new actions will then be available at the urls `^users/{pk}/set_password/$` and `^users/{pk}/unset_password/$`. Use the `url_path` and `url_name` parameters to change the URL segement and the reverse URL name of the action.

To view all extra actions, call the `.get_extra_actions()` method.

### Routing additional HTTP methods for extra actions

Extra actions can map additional HTTP methods to separate `ViewSet` methods. For example, the above password set/unset methods could be consolidated into a single route. Note that additional mappings do not accept arguments.

```python
    @action(detail=True, methods=['put'], name='Change Password')
    def password(self, request, pk=None):
        """Update the user's password."""
        ...

    @password.mapping.delete
    def delete_password(self, request, pk=None):
        """Delete the user's password."""
        ...
```

## Reversing action URLs

If you need to get the URL of an action, use the `.reverse_action()` method. This is a convenience wrapper for `reverse()`, automatically passing the view's `request` object and prepending the `url_name` with the `.basename` attribute.

Note that the `basename` is provided by the router during `ViewSet` registration. If you are not using a router, then you must provide the `basename` argument to the `.as_view()` method.

Using the example from the previous section:

```python
>>> view.reverse_action('set-password', args=['1'])
'http://localhost:8000/api/users/1/set_password'
```

Alternatively, you can use the `url_name` attribute set by the `@action` decorator.

```python
>>> view.reverse_action(view.set_password.url_name, args=['1'])
'http://localhost:8000/api/users/1/set_password'
```

The `url_name` argument for `.reverse_action()` should match the same argument to the `@action` decorator. Additionally, this method can be used to reverse the default actions, such as `list` and `create`.

---

# API Reference

## ViewSet

The `ViewSet` class inherits from `APIView`.  You can use any of the standard attributes such as `permission_classes`, `authentication_classes` in order to control the API policy on the viewset.

The `ViewSet` class does not provide any implementations of actions.  In order to use a `ViewSet` class you'll override the class and define the action implementations explicitly.

## GenericViewSet

The `GenericViewSet` class inherits from `GenericAPIView`, and provides the default set of `get_object`, `get_queryset` methods and other generic view base behavior, but does not include any actions by default.

In order to use a `GenericViewSet` class you'll override the class and either mixin the required mixin classes, or define the action implementations explicitly.

## ModelViewSet

The `ModelViewSet` class inherits from `GenericAPIView` and includes implementations for various actions, by mixing in the behavior of the various mixin classes.

The actions provided by the `ModelViewSet` class are `.list()`, `.retrieve()`,  `.create()`, `.update()`, `.partial_update()`, and `.destroy()`.

#### Example

Because `ModelViewSet` extends `GenericAPIView`, you'll normally need to provide at least the `queryset` and `serializer_class` attributes.  For example:

    class AccountViewSet(viewsets.ModelViewSet):
        """
        A simple ViewSet for viewing and editing accounts.
        """
        queryset = Account.objects.all()
        serializer_class = AccountSerializer
        permission_classes = [IsAccountAdminOrReadOnly]

Note that you can use any of the standard attributes or method overrides provided by `GenericAPIView`.  For example, to use a `ViewSet` that dynamically determines the queryset it should operate on, you might do something like this:

    class AccountViewSet(viewsets.ModelViewSet):
        """
        A simple ViewSet for viewing and editing the accounts
        associated with the user.
        """
        serializer_class = AccountSerializer
        permission_classes = [IsAccountAdminOrReadOnly]

        def get_queryset(self):
            return self.request.user.accounts.all()

Note however that upon removal of the `queryset` property from your `ViewSet`, any associated [router][routers] will be unable to derive the basename of your Model automatically, and so you will have to specify the `basename` kwarg as part of your [router registration][routers].

Also note that although this class provides the complete set of create/list/retrieve/update/destroy actions by default, you can restrict the available operations by using the standard permission classes.

## ReadOnlyModelViewSet

The `ReadOnlyModelViewSet` class also inherits from `GenericAPIView`.  As with `ModelViewSet` it also includes implementations for various actions, but unlike `ModelViewSet` only provides the 'read-only' actions, `.list()` and `.retrieve()`.

#### Example

As with `ModelViewSet`, you'll normally need to provide at least the `queryset` and `serializer_class` attributes.  For example:

    class AccountViewSet(viewsets.ReadOnlyModelViewSet):
        """
        A simple ViewSet for viewing accounts.
        """
        queryset = Account.objects.all()
        serializer_class = AccountSerializer

Again, as with `ModelViewSet`, you can use any of the standard attributes and method overrides available to `GenericAPIView`.

# Custom ViewSet base classes

You may need to provide custom `ViewSet` classes that do not have the full set of `ModelViewSet` actions, or that customize the behavior in some other way.

## Example

To create a base viewset class that provides `create`, `list` and `retrieve` operations, inherit from `GenericViewSet`, and mixin the required actions:

    from rest_framework import mixins

    class CreateListRetrieveViewSet(mixins.CreateModelMixin,
                                    mixins.ListModelMixin,
                                    mixins.RetrieveModelMixin,
                                    viewsets.GenericViewSet):
        """
        A viewset that provides `retrieve`, `create`, and `list` actions.

        To use it, override the class and set the `.queryset` and
        `.serializer_class` attributes.
        """
        pass

By creating your own base `ViewSet` classes, you can provide common behavior that can be reused in multiple viewsets across your API.

[cite]: https://guides.rubyonrails.org/action_controller_overview.html
[routers]: routers.md
