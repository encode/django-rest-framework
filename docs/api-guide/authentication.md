# Authentication

Authentication is the mechanism of associating an incoming request with a set of identifying credentials, such as the user the request came from, or the token that it was signed with.  The [permission] and [throttling] policies can then use those credentials to determine if the request should be permitted.

REST framework provides a number of authentication policies out of the box, and also allows you to implement custom policies.

Authentication will run the first time either the `request.user` or `request.auth` properties are accessed, and determines how those properties are initialized.

The `request.user` property will typically be set to an instance of the `contrib.auth` package's `User` class.

The `request.auth` property is used for any additional authentication information, for example, it may be used to represent an authentication token that the request was signed with.

## How authentication is determined

Authentication is always set as a list of classes.  REST framework will attempt to authenticate with each class in the list, and will set `request.user` and `request.auth` using the return value of the first class that successfully authenticates.

If no class authenticates, `request.user` will be set to an instance of `django.contrib.auth.models.AnonymousUser`, and `request.auth` will be set to `None`.

The value of `request.user` and `request.auth` for unauthenticated requests can be modified using the `UNAUTHENTICATED_USER` and `UNAUTHENTICATED_TOKEN` settings.

## Setting the authentication policy

The default authentication policy may be set globally, using the `DEFAULT_AUTHENTICATION` setting.  For example.

    API_SETTINGS = {
        'DEFAULT_AUTHENTICATION': (
            'djangorestframework.authentication.UserBasicAuthentication',
            'djangorestframework.authentication.SessionAuthentication',
        )
    }

You can also set the authentication policy on a per-view basis, using the `APIView` class based views.

    class ExampleView(APIView):
        authentication_classes = (SessionAuthentication, UserBasicAuthentication)

        def get(self, request, format=None):
            content = {
                'user': unicode(request.user),  # `django.contrib.auth.User` instance.
                'auth': unicode(request.auth),  # None
            }
            return Response(content)

Or, if you're using the `@api_view` decorator with function based views.

    @api_view(
        allowed=('GET',),
        authentication_classes=(SessionAuthentication, UserBasicAuthentication)
    )
    def example_view(request, format=None):
        content = {
            'user': unicode(request.user),  # `django.contrib.auth.User` instance.
            'auth': unicode(request.auth),  # None
        }
        return Response(content)

## UserBasicAuthentication

This policy uses [HTTP Basic Authentication][basicauth], signed against a user's username and password.  User basic authentication is generally only appropriate for testing.

**Note:** If you run `UserBasicAuthentication` in production your API must be `https` only, or it will be completely insecure.  You should also ensure that your API clients will always re-request the username and password at login, and will never store those details to persistent storage.

If successfully authenticated, `UserBasicAuthentication` provides the following credentials.

* `request.user` will be a `django.contrib.auth.models.User` instance.
* `request.auth` will be `None`.

## TokenAuthentication

This policy uses [HTTP Authentication][basicauth] with no authentication scheme.  Token basic authentication is appropriate for client-server setups, such as native desktop and mobile clients.  The token key should be passed in as a string to the "Authorization" HTTP header.  For example:

    curl http://my.api.org/ -X POST -H "Authorization: 0123456789abcdef0123456789abcdef"

**Note:** If you run `TokenAuthentication` in production your API must be `https` only, or it will be completely insecure.

If successfully authenticated, `TokenAuthentication` provides the following credentials.

* `request.user` will be a `django.contrib.auth.models.User` instance.
* `request.auth` will be a `djangorestframework.tokenauth.models.BasicToken` instance.

To use the `TokenAuthentication` policy, you must have a token model.  Django REST Framework comes with a minimal default token model.  To use it, include `djangorestframework.tokenauth` in your installed applications and sync your database.  To use your own token model, subclass the `djangorestframework.tokenauth.TokenAuthentication` class and specify a `model` attribute that references your custom token model.  The token model must provide `user`, `key`, and `revoked` attributes.  Refer to the `djangorestframework.tokenauth.models.BasicToken` model as an example.

## OAuthAuthentication

This policy uses the [OAuth 2.0][oauth] protocol to authenticate requests.  OAuth is appropriate for server-server setups, such as when you want to allow a third-party service to access your API on a user's behalf.

If successfully authenticated, `OAuthAuthentication` provides the following credentials.

* `request.user` will be a `django.contrib.auth.models.User` instance.
* `request.auth` will be a `djangorestframework.models.OAuthToken` instance.

## SessionAuthentication

This policy uses Django's default session backend for authentication.  Session authentication is appropriate for AJAX clients that are running in the same session context as your website.

If successfully authenticated, `SessionAuthentication` provides the following credentials.

* `request.user` will be a `django.contrib.auth.models.User` instance.
* `request.auth` will be `None`.

## Custom authentication policies

To implement a custom authentication policy, subclass `BaseAuthentication` and override the `authenticate(self, request)` method.  The method should return a two-tuple of `(user, auth)` if authentication succeeds, or `None` otherwise.

[basicauth]: http://tools.ietf.org/html/rfc2617
[oauth]: http://oauth.net/2/
[permission]: permissions.md
[throttling]: throttling.md
