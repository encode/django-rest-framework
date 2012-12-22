<a class="github" href="authentication.py"></a>

# Authentication

> Auth needs to be pluggable.
>
> &mdash; Jacob Kaplan-Moss, ["REST worst practices"][cite]

Authentication is the mechanism of associating an incoming request with a set of identifying credentials, such as the user the request came from, or the token that it was signed with.  The [permission] and [throttling] policies can then use those credentials to determine if the request should be permitted.

REST framework provides a number of authentication policies out of the box, and also allows you to implement custom policies.

Authentication will run the first time either the `request.user` or `request.auth` properties are accessed, and determines how those properties are initialized.

The `request.user` property will typically be set to an instance of the `contrib.auth` package's `User` class.

The `request.auth` property is used for any additional authentication information, for example, it may be used to represent an authentication token that the request was signed with.

## How authentication is determined

The authentication policy is always defined as a list of classes.  REST framework will attempt to authenticate with each class in the list, and will set `request.user` and `request.auth` using the return value of the first class that successfully authenticates.

If no class authenticates, `request.user` will be set to an instance of `django.contrib.auth.models.AnonymousUser`, and `request.auth` will be set to `None`.

The value of `request.user` and `request.auth` for unauthenticated requests can be modified using the `UNAUTHENTICATED_USER` and `UNAUTHENTICATED_TOKEN` settings.

## Setting the authentication policy

The default authentication policy may be set globally, using the `DEFAULT_AUTHENTICATION_CLASSES` setting.  For example.

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
        )
    }

You can also set the authentication policy on a per-view basis, using the `APIView` class based views.

    class ExampleView(APIView):
        authentication_classes = (SessionAuthentication, BasicAuthentication)
        permission_classes = (IsAuthenticated,)

        def get(self, request, format=None):
            content = {
                'user': unicode(request.user),  # `django.contrib.auth.User` instance.
                'auth': unicode(request.auth),  # None
            }
            return Response(content)

Or, if you're using the `@api_view` decorator with function based views.

    @api_view(['GET'])
    @authentication_classes((SessionAuthentication, BasicAuthentication))
    @permissions_classes((IsAuthenticated,))
    def example_view(request, format=None):
        content = {
            'user': unicode(request.user),  # `django.contrib.auth.User` instance.
            'auth': unicode(request.auth),  # None
        }
        return Response(content)

# API Reference

## BasicAuthentication

This policy uses [HTTP Basic Authentication][basicauth], signed against a user's username and password.  Basic authentication is generally only appropriate for testing.

If successfully authenticated, `BasicAuthentication` provides the following credentials.

* `request.user` will be a Django `User` instance.
* `request.auth` will be `None`.

**Note:** If you use `BasicAuthentication` in production you must ensure that your API is only available over `https` only.  You should also ensure that your API clients will always re-request the username and password at login, and will never store those details to persistent storage.

## TokenAuthentication

This policy uses a simple token-based HTTP Authentication scheme.  Token authentication is appropriate for client-server setups, such as native desktop and mobile clients.

To use the `TokenAuthentication` policy, include `rest_framework.authtoken` in your `INSTALLED_APPS` setting.

You'll also need to create tokens for your users.

    from rest_framework.authtoken.models import Token

    token = Token.objects.create(user=...)
    print token.key

For clients to authenticate, the token key should be included in the `Authorization` HTTP header.  The key should be prefixed by the string literal "Token", with whitespace separating the two strings.  For example:

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

If successfully authenticated, `TokenAuthentication` provides the following credentials.

* `request.user` will be a Django `User` instance.
* `request.auth` will be a `rest_framework.tokenauth.models.BasicToken` instance.

**Note:** If you use `TokenAuthentication` in production you must ensure that your API is only available over `https` only.

If you want every user to have an automatically generated Token, you can simply catch the User's `post_save` signal.

    @receiver(post_save, sender=User)
    def create_auth_token(sender, instance=None, created=False, **kwargs):
        if created:
            Token.objects.create(user=instance)

If you've already created some users, you can generate tokens for all existing users like this:

    from django.contrib.auth.models import User
    from rest_framework.authtoken.models import Token

    for user in User.objects.all():
        Token.objects.get_or_create(user=user)

When using `TokenAuthentication`, you may want to provide a mechanism for clients to obtain a token given the username and password. 
REST framework provides a built-in view to provide this behavior.  To use it, add the `obtain_auth_token` view to your URLconf:

    urlpatterns += patterns('',
        url(r'^api-token-auth/', 'rest_framework.authtoken.views.obtain_auth_token')
    )

Note that the URL part of the pattern can be whatever you want to use.

The `obtain_auth_token` view will return a JSON response when valid `username` and `password` fields are POSTed to the view using form data or JSON:

    { 'token' : '9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' }

<!--
## OAuthAuthentication

This policy uses the [OAuth 2.0][oauth] protocol to authenticate requests.  OAuth is appropriate for server-server setups, such as when you want to allow a third-party service to access your API on a user's behalf.

If successfully authenticated, `OAuthAuthentication` provides the following credentials.

* `request.user` will be a Django `User` instance.
* `request.auth` will be a `rest_framework.models.OAuthToken` instance.
-->

## SessionAuthentication

This policy uses Django's default session backend for authentication.  Session authentication is appropriate for AJAX clients that are running in the same session context as your website.

If successfully authenticated, `SessionAuthentication` provides the following credentials.

* `request.user` will be a Django `User` instance.
* `request.auth` will be `None`.

# Custom authentication

To implement a custom authentication policy, subclass `BaseAuthentication` and override the `.authenticate(self, request)` method.  The method should return a two-tuple of `(user, auth)` if authentication succeeds, or `None` otherwise.

[cite]: http://jacobian.org/writing/rest-worst-practices/
[basicauth]: http://tools.ietf.org/html/rfc2617
[oauth]: http://oauth.net/2/
[permission]: permissions.md
[throttling]: throttling.md
