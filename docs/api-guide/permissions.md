<a class="github" href="permissions.py"></a>

# Permissions

> Authentication or identification by itself is not usually sufficient to gain access to information or code.  For that, the entity requesting access must have authorization.
>
> &mdash; [Apple Developer Documentation][cite]

Together with [authentication] and [throttling], permissions determine whether a request should be granted or denied access.

Permission checks are always run at the very start of the view, before any other code is allowed to proceed.  Permission checks will typically use the authentication information in the `request.user` and `request.auth` properties to determine if the incoming request should be permitted.

## How permissions are determined

Permissions in REST framework are always defined as a list of permission classes.  

Before running the main body of the view each permission in the list is checked.
If any permission check fails an `exceptions.PermissionDenied` exception will be raised, and the main body of the view will not run.

## Object level permissions

REST framework permissions also support object-level permissioning.  Object level permissions are used to determine if a user should be allowed to act on a particular object, which will typically be a model instance.

Object level permissions are run by REST framework's generic views when `.get_object()` is called.
As with view level permissions, an `exceptions.PermissionDenied` exception will be raised if the user is not allowed to act on the given object.

If you're writing your own views and want to enforce object level permissions,
you'll need to explicitly call the `.check_object_permissions(request, obj)` method on the view at the point at which you've retrieved the object.
This will either raise a `PermissionDenied` or `NotAuthenticated` exception, or simply return if the view has the appropriate permissions.

## Setting the permission policy

The default permission policy may be set globally, using the `DEFAULT_PERMISSION_CLASSES` setting.  For example.

    REST_FRAMEWORK = {
        'DEFAULT_PERMISSION_CLASSES': (
            'rest_framework.permissions.IsAuthenticated',
        )
    }

If not specified, this setting defaults to allowing unrestricted access:

    'DEFAULT_PERMISSION_CLASSES': (
       'rest_framework.permissions.AllowAny',
    )

You can also set the authentication policy on a per-view, or per-viewset basis,
using the `APIView` class based views.

    class ExampleView(APIView):
        permission_classes = (IsAuthenticated,)

        def get(self, request, format=None):
            content = {
                'status': 'request was permitted'
            }
            return Response(content)

Or, if you're using the `@api_view` decorator with function based views.

    @api_view('GET')
    @permission_classes((IsAuthenticated, ))
    def example_view(request, format=None):
        content = {
            'status': 'request was permitted'
        }
        return Response(content)

---

# API Reference

## AllowAny

The `AllowAny` permission class will allow unrestricted access, **regardless of if the request was authenticated or unauthenticated**.

This permission is not strictly required, since you can achieve the same result by using an empty list or tuple for the permissions setting, but you may find it useful to specify this class because it makes the intention explicit.

## IsAuthenticated

The `IsAuthenticated` permission class will deny permission to any unauthenticated user, and allow permission otherwise.

This permission is suitable if you want your API to only be accessible to registered users.

## IsAdminUser

The `IsAdminUser` permission class will deny permission to any user, unless `user.is_staff` is `True` in which case permission will be allowed.

This permission is suitable is you want your API to only be accessible to a subset of trusted administrators.

## IsAuthenticatedOrReadOnly

The `IsAuthenticatedOrReadOnly` will allow authenticated users to perform any request.  Requests for unauthorised users will only be permitted if the request method is one of the "safe" methods; `GET`, `HEAD` or `OPTIONS`.

This permission is suitable if you want to your API to allow read permissions to anonymous users, and only allow write permissions to authenticated users.

## DjangoModelPermissions

This permission class ties into Django's standard `django.contrib.auth` [model permissions][contribauth].  When applied to a view that has a `.model` property, authorization will only be granted if the user *is authenticated* and has the *relevant model permissions* assigned.

* `POST` requests require the user to have the `add` permission on the model.
* `PUT` and `PATCH` requests require the user to have the `change` permission on the model.
* `DELETE` requests require the user to have the `delete` permission on the model.

The default behaviour can also be overridden to support custom model permissions.  For example, you might want to include a `view` model permission for `GET` requests.

To use custom model permissions, override `DjangoModelPermissions` and set the `.perms_map` property.  Refer to the source code for details.

## DjangoModelPermissionsOrAnonReadOnly

Similar to `DjangoModelPermissions`, but also allows unauthenticated users to have  read-only access to the API.

## TokenHasReadWriteScope

This permission class is intended for use with either of the `OAuthAuthentication` and `OAuth2Authentication` classes, and ties into the scoping that their backends provide.

Requests with a safe methods of `GET`, `OPTIONS` or `HEAD` will be allowed if the authenticated token has read permission.

Requests for `POST`, `PUT`, `PATCH` and `DELETE` will be allowed if the authenticated token has write permission.

This permission class relies on the implementations of the [django-oauth-plus][django-oauth-plus] and [django-oauth2-provider][django-oauth2-provider] libraries, which both provide limited support for controlling the scope of access tokens:

* `django-oauth-plus`: Tokens are associated with a `Resource` class which has a `name`, `url` and `is_readonly` properties.
* `django-oauth2-provider`: Tokens are associated with a bitwise `scope` attribute, that defaults to providing bitwise values for `read` and/or `write`.

If you require more advanced scoping for your API, such as restricting tokens to accessing a subset of functionality of your API then you will need to provide a custom permission class.  See the source of the `django-oauth-plus` or `django-oauth2-provider` package for more details on scoping token access.

---

# Custom permissions

To implement a custom permission, override `BasePermission` and implement either, or both, of the following methods:

* `.has_permission(self, request, view)`
* `.has_object_permission(self, request, view, obj)`

The methods should return `True` if the request should be granted access, and `False` otherwise.

If you need to test if a request is a read operation or a write operation, you should check the request method against the constant `SAFE_METHODS`, which is a tuple containing `'GET'`, `'OPTIONS'` and `'HEAD'`.  For example:

    if request.method in permissions.SAFE_METHODS:
        # Check permissions for read-only request
    else:
        # Check permissions for write request

---

**Note**: In versions 2.0 and 2.1, the signature for the permission checks always included an optional `obj` parameter, like so: `.has_permission(self, request, view, obj=None)`.  The method would be called twice, first for the global permission checks, with no object supplied, and second for the object-level check when required.

As of version 2.2 this signature has now been replaced with two separate method calls, which is more explict and obvious.  The old style signature continues to work, but it's use will result in a `PendingDeprecationWarning`, which is silent by default.  In 2.3 this will be escalated to a `DeprecationWarning`, and in 2.4 the old-style signature will be removed.

For more details see the [2.2 release announcement][2.2-announcement].

---

## Examples

The following is an example of a permission class that checks the incoming request's IP address against a blacklist, and denies the request if the IP has been blacklisted.

    class BlacklistPermission(permissions.BasePermission):
        """
        Global permission check for blacklisted IPs.
        """

        def has_permission(self, request, view):
            ip_addr = request.META['REMOTE_ADDR']
            blacklisted = Blacklist.objects.filter(ip_addr=ip_addr).exists()
            return not blacklisted

As well as global permissions, that are run against all incoming requests, you can also create object-level permissions, that are only run against operations that affect a particular object instance.  For example:

    class IsOwnerOrReadOnly(permissions.BasePermission):
        """
        Object-level permission to only allow owners of an object to edit it.
        Assumes the model instance has an `owner` attribute.
        """

        def has_object_permission(self, request, view, obj):
            # Read permissions are allowed to any request,
            # so we'll always allow GET, HEAD or OPTIONS requests.
            if request.method in permissions.SAFE_METHODS:            
                return True
    
            # Instance must have an attribute named `owner`.
            return obj.owner == request.user

Note that the generic views will check the appropriate object level permissions, but if you're writing your own custom views, you'll need to make sure you check the object level permission checks yourself.  You can do so by calling `self.check_object_permissions(request, obj)` from the view once you have the object instance.  This call will raise an appropriate `APIException` if any object-level permission checks fail, and will otherwise simply return.

Also note that the generic views will only check the object-level permissions for views that retrieve a single model instance.  If you require object-level filtering of list views, you'll need to filter the queryset separately.  See the [filtering documentation][filtering] for more details.

[cite]: https://developer.apple.com/library/mac/#documentation/security/Conceptual/AuthenticationAndAuthorizationGuide/Authorization/Authorization.html
[authentication]: authentication.md
[throttling]: throttling.md
[contribauth]: https://docs.djangoproject.com/en/1.0/topics/auth/#permissions
[guardian]: https://github.com/lukaszb/django-guardian
[django-oauth-plus]: http://code.larlet.fr/django-oauth-plus
[django-oauth2-provider]: https://github.com/caffeinehit/django-oauth2-provider
[2.2-announcement]: ../topics/2.2-announcement.md
[filtering]: filtering.md
