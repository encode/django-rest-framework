<a class="github" href="authentication.py"></a>

# Authentication

> Auth needs to be pluggable.
>
> &mdash; Jacob Kaplan-Moss, ["REST worst practices"][cite]

Authentication is the mechanism of associating an incoming request with a set of identifying credentials, such as the user the request came from, or the token that it was signed with.  The [permission] and [throttling] policies can then use those credentials to determine if the request should be permitted.

REST framework provides a number of authentication schemes out of the box, and also allows you to implement custom schemes.

Authentication will run the first time either the `request.user` or `request.auth` properties are accessed, and determines how those properties are initialized.

The `request.user` property will typically be set to an instance of the `contrib.auth` package's `User` class.

The `request.auth` property is used for any additional authentication information, for example, it may be used to represent an authentication token that the request was signed with.

---

**Note:** Don't forget that **authentication by itself won't allow or disallow an incoming request**, it simply identifies the credentials that the request was made with.

For information on how to setup the permission polices for your API please see the [permissions documentation][permission].

---

## How authentication is determined

The authentication schemes are always defined as a list of classes.  REST framework will attempt to authenticate with each class in the list, and will set `request.user` and `request.auth` using the return value of the first class that successfully authenticates.

If no class authenticates, `request.user` will be set to an instance of `django.contrib.auth.models.AnonymousUser`, and `request.auth` will be set to `None`.

The value of `request.user` and `request.auth` for unauthenticated requests can be modified using the `UNAUTHENTICATED_USER` and `UNAUTHENTICATED_TOKEN` settings.

## Setting the authentication scheme

The default authentication schemes may be set globally, using the `DEFAULT_AUTHENTICATION` setting.  For example.

    REST_FRAMEWORK = {
        'DEFAULT_AUTHENTICATION_CLASSES': (
            'rest_framework.authentication.BasicAuthentication',
            'rest_framework.authentication.SessionAuthentication',
        )
    }

You can also set the authentication scheme on a per-view basis, using the `APIView` class based views.

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
    @permission_classes((IsAuthenticated,))
    def example_view(request, format=None):
        content = {
            'user': unicode(request.user),  # `django.contrib.auth.User` instance.
            'auth': unicode(request.auth),  # None
        }
        return Response(content)

## Unauthorized and Forbidden responses

When an unauthenticated request is denied permission there are two different error codes that may be appropriate.

* [HTTP 401 Unauthorized][http401]
* [HTTP 403 Permission Denied][http403]

HTTP 401 responses must always include a `WWW-Authenticate` header, that instructs the client how to authenticate.  HTTP 403 responses do not include the `WWW-Authenticate` header.

The kind of response that will be used depends on the authentication scheme.  Although multiple authentication schemes may be in use, only one scheme may be used to determine the type of response.  **The first authentication class set on the view is used when determining the type of response**.

Note that when a request may successfully authenticate, but still be denied permission to perform the request, in which case a `403 Permission Denied` response will always be used, regardless of the authentication scheme.

## Apache mod_wsgi specific configuration

Note that if deploying to [Apache using mod_wsgi][mod_wsgi_official], the authorization header is not passed through to a WSGI application by default, as it is assumed that authentication will be handled by Apache, rather than at an application level.

If you are deploying to Apache, and using any non-session based authentication, you will need to explicitly configure mod_wsgi to pass the required headers through to the application. This can be done by specifying the `WSGIPassAuthorization` directive in the appropriate context and setting it to `'On'`.

    # this can go in either server config, virtual host, directory or .htaccess 
    WSGIPassAuthorization On

---

# API Reference

## BasicAuthentication

This authentication scheme uses [HTTP Basic Authentication][basicauth], signed against a user's username and password.  Basic authentication is generally only appropriate for testing.

If successfully authenticated, `BasicAuthentication` provides the following credentials.

* `request.user` will be a Django `User` instance.
* `request.auth` will be `None`.

Unauthenticated responses that are denied permission will result in an `HTTP 401 Unauthorized` response with an appropriate WWW-Authenticate header.  For example:

    WWW-Authenticate: Basic realm="api"

**Note:** If you use `BasicAuthentication` in production you must ensure that your API is only available over `https` only.  You should also ensure that your API clients will always re-request the username and password at login, and will never store those details to persistent storage.

## TokenAuthentication

This authentication scheme uses a simple token-based HTTP Authentication scheme.  Token authentication is appropriate for client-server setups, such as native desktop and mobile clients.

To use the `TokenAuthentication` scheme, include `rest_framework.authtoken` in your `INSTALLED_APPS` setting.

You'll also need to create tokens for your users.

    from rest_framework.authtoken.models import Token

    token = Token.objects.create(user=...)
    print token.key

For clients to authenticate, the token key should be included in the `Authorization` HTTP header.  The key should be prefixed by the string literal "Token", with whitespace separating the two strings.  For example:

    Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b

If successfully authenticated, `TokenAuthentication` provides the following credentials.

* `request.user` will be a Django `User` instance.
* `request.auth` will be a `rest_framework.authtoken.models.BasicToken` instance.

Unauthenticated responses that are denied permission will result in an `HTTP 401 Unauthorized` response with an appropriate WWW-Authenticate header.  For example:

    WWW-Authenticate: Token

**Note:** If you use `TokenAuthentication` in production you must ensure that your API is only available over `https` only.

=======
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

## SessionAuthentication

This authentication scheme uses Django's default session backend for authentication.  Session authentication is appropriate for AJAX clients that are running in the same session context as your website.

If successfully authenticated, `SessionAuthentication` provides the following credentials.

* `request.user` will be a Django `User` instance.
* `request.auth` will be `None`.

Unauthenticated responses that are denied permission will result in an `HTTP 403 Forbidden` response.

If you're using an AJAX style API with SessionAuthentication, you'll need to make sure you include a valid CSRF token for any "unsafe" HTTP method calls, such as `PUT`, `POST` or `DELETE` requests.  See the [Django CSRF documentation][csrf-ajax] for more details.

# Custom authentication

To implement a custom authentication scheme, subclass `BaseAuthentication` and override the `.authenticate(self, request)` method.  The method should return a two-tuple of `(user, auth)` if authentication succeeds, or `None` otherwise.

In some circumstances instead of returning `None`, you may want to raise an `AuthenticationFailed` exception from the `.authenticate()` method.

Typically the approach you should take is:

* If authentication is not attempted, return `None`.  Any other authentication schemes also in use will still be checked.
* If authentication is attempted but fails, raise a `AuthenticationFailed` exception.  An error response will be returned immediately, without checking any other authentication schemes.

You *may* also override the `.authentication_header(self, request)` method.  If implemented, it should return a string that will be used as the value of the `WWW-Authenticate` header in a `HTTP 401 Unauthorized` response.

If the `.authentication_header()` method is not overridden, the authentication scheme will return `HTTP 403 Forbidden` responses when an unauthenticated request is denied access.

[cite]: http://jacobian.org/writing/rest-worst-practices/
[http401]: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.2
[http403]: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.4
[basicauth]: http://tools.ietf.org/html/rfc2617
[oauth]: http://oauth.net/2/
[permission]: permissions.md
[throttling]: throttling.md
[csrf-ajax]: https://docs.djangoproject.com/en/dev/ref/contrib/csrf/#ajax
[mod_wsgi_official]: http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIPassAuthorization
