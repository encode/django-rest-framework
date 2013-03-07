"""
Provides a set of pluggable authentication policies.
"""
from __future__ import unicode_literals
from django.contrib.auth import authenticate
from django.core.exceptions import ImproperlyConfigured
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework.compat import CsrfViewMiddleware
from rest_framework.compat import oauth, oauth_provider, oauth_provider_store
from rest_framework.compat import oauth2_provider, oauth2_provider_forms, oauth2_provider_backends
from rest_framework.authtoken.models import Token
import base64


class BaseAuthentication(object):
    """
    All authentication classes should extend BaseAuthentication.
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        raise NotImplementedError(".authenticate() must be overridden.")

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        pass


class BasicAuthentication(BaseAuthentication):
    """
    HTTP Basic authentication against username/password.
    """
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Returns a `User` if a correct username and password have been supplied
        using HTTP Basic authentication.  Otherwise returns `None`.
        """
        auth = request.META.get('HTTP_AUTHORIZATION', b'')
        if type(auth) == type(''):
            # Work around django test client oddness
            auth = auth.encode(HTTP_HEADER_ENCODING)
        auth = auth.split()

        if not auth or auth[0].lower() != b'basic':
            return None

        if len(auth) != 2:
            raise exceptions.AuthenticationFailed('Invalid basic header')

        try:
            auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(':')
        except (TypeError, UnicodeDecodeError):
            raise exceptions.AuthenticationFailed('Invalid basic header')

        userid, password = auth_parts[0], auth_parts[2]
        return self.authenticate_credentials(userid, password)

    def authenticate_credentials(self, userid, password):
        """
        Authenticate the userid and password against username and password.
        """
        user = authenticate(username=userid, password=password)
        if user is not None and user.is_active:
            return (user, None)
        raise exceptions.AuthenticationFailed('Invalid username/password')

    def authenticate_header(self, request):
        return 'Basic realm="%s"' % self.www_authenticate_realm


class SessionAuthentication(BaseAuthentication):
    """
    Use Django's session framework for authentication.
    """

    def authenticate(self, request):
        """
        Returns a `User` if the request session currently has a logged in user.
        Otherwise returns `None`.
        """

        # Get the underlying HttpRequest object
        http_request = request._request
        user = getattr(http_request, 'user', None)

        # Unauthenticated, CSRF validation not required
        if not user or not user.is_active:
            return None

        # Enforce CSRF validation for session based authentication.
        class CSRFCheck(CsrfViewMiddleware):
            def _reject(self, request, reason):
                # Return the failure reason instead of an HttpResponse
                return reason

        reason = CSRFCheck().process_view(http_request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.AuthenticationFailed('CSRF Failed: %s' % reason)

        # CSRF passed with authenticated user
        return (user, None)


class TokenAuthentication(BaseAuthentication):
    """
    Simple token based authentication.

    Clients should authenticate by passing the token key in the "Authorization"
    HTTP header, prepended with the string "Token ".  For example:

        Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    model = Token
    """
    A custom token model may be used, but must have the following properties.

    * key -- The string identifying the token
    * user -- The user to which the token belongs
    """

    def authenticate(self, request):
        auth = request.META.get('HTTP_AUTHORIZATION', '').split()

        if not auth or auth[0].lower() != "token":
            return None

        if len(auth) != 2:
            raise exceptions.AuthenticationFailed('Invalid token header')

        return self.authenticate_credentials(auth[1])

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        if token.user.is_active:
            return (token.user, token)
        raise exceptions.AuthenticationFailed('User inactive or deleted')

    def authenticate_header(self, request):
        return 'Token'


class OAuthAuthentication(BaseAuthentication):
    """
    OAuth 1.0a authentication backend using `django-oauth-plus` and `oauth2`.

    Note: The `oauth2` package actually provides oauth1.0a support.  Urg.
          We import it from the `compat` module as `oauth`.
    """
    www_authenticate_realm = 'api'

    def __init__(self, **kwargs):
        super(OAuthAuthentication, self).__init__(**kwargs)

        if oauth is None:
            raise ImproperlyConfigured(
                "The 'oauth2' package could not be imported."
                "It is required for use with the 'OAuthAuthentication' class.")

        if oauth_provider is None:
            raise ImproperlyConfigured(
                "The 'django-oauth-plus' package could not be imported."
                "It is required for use with the 'OAuthAuthentication' class.")

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """
        try:
            oauth_request = oauth_provider.utils.get_oauth_request(request)
        except oauth.Error as err:
            raise exceptions.AuthenticationFailed(err.message)

        oauth_params = oauth_provider.consts.OAUTH_PARAMETERS_NAMES

        found = any(param for param in oauth_params if param in oauth_request)
        missing = list(param for param in oauth_params if param not in oauth_request)

        if not found:
            # OAuth authentication was not attempted.
            return None

        if missing:
            # OAuth was attempted but missing parameters.
            msg = 'Missing parameters: %s' % (', '.join(missing))
            raise exceptions.AuthenticationFailed(msg)

        if not self.check_nonce(request, oauth_request):
            msg = 'Nonce check failed'
            raise exceptions.AuthenticationFailed(msg)

        try:
            consumer_key = oauth_request.get_parameter('oauth_consumer_key')
            consumer = oauth_provider_store.get_consumer(request, oauth_request, consumer_key)
        except oauth_provider_store.InvalidConsumerError as err:
            raise exceptions.AuthenticationFailed(err)

        if consumer.status != oauth_provider.consts.ACCEPTED:
            msg = 'Invalid consumer key status: %s' % consumer.get_status_display()
            raise exceptions.AuthenticationFailed(msg)

        try:
            token_param = oauth_request.get_parameter('oauth_token')
            token = oauth_provider_store.get_access_token(request, oauth_request, consumer, token_param)
        except oauth_provider_store.InvalidTokenError:
            msg = 'Invalid access token: %s' % oauth_request.get_parameter('oauth_token')
            raise exceptions.AuthenticationFailed(msg)

        try:
            self.validate_token(request, consumer, token)
        except oauth.Error as err:
            raise exceptions.AuthenticationFailed(err.message)

        user = token.user

        if not user.is_active:
            msg = 'User inactive or deleted: %s' % user.username
            raise exceptions.AuthenticationFailed(msg)

        return (token.user, token)

    def authenticate_header(self, request):
        """
        If permission is denied, return a '401 Unauthorized' response,
        with an appropraite 'WWW-Authenticate' header.
        """
        return 'OAuth realm="%s"' % self.www_authenticate_realm

    def validate_token(self, request, consumer, token):
        """
        Check the token and raise an `oauth.Error` exception if invalid.
        """
        oauth_server, oauth_request = oauth_provider.utils.initialize_server_request(request)
        oauth_server.verify_request(oauth_request, consumer, token)

    def check_nonce(self, request, oauth_request):
        """
        Checks nonce of request, and return True if valid.
        """
        return oauth_provider_store.check_nonce(request, oauth_request, oauth_request['oauth_nonce'])


class OAuth2Authentication(BaseAuthentication):
    """
    OAuth 2 authentication backend using `django-oauth2-provider`
    """
    require_active = True

    def __init__(self, **kwargs):
        super(OAuth2Authentication, self).__init__(**kwargs)
        if oauth2_provider is None:
            raise ImproperlyConfigured("The 'django-oauth2-provider' package could not be imported. It is required for use with the 'OAuth2Authentication' class.")

    def authenticate(self, request):
        """
        The Bearer type is the only finalized type

        Read the spec for more details
        http://tools.ietf.org/html/rfc6749#section-7.1
        """
        auth = request.META.get('HTTP_AUTHORIZATION', '').split()
        if not auth or auth[0].lower() != "bearer":
            raise exceptions.AuthenticationFailed('Invalid Authorization token type')

        if len(auth) != 2:
            raise exceptions.AuthenticationFailed('Invalid token header')

        return self.authenticate_credentials(request, auth[1])

    def authenticate_credentials(self, request, access_token):
        """
        :returns: two-tuple of (user, auth) if authentication succeeds, or None otherwise.
        """

        # authenticate the client
        oauth2_client_form = oauth2_provider_forms.ClientAuthForm(request.REQUEST)
        if not oauth2_client_form.is_valid():
            raise exceptions.AuthenticationFailed("Client could not be validated")
        client = oauth2_client_form.cleaned_data.get('client')

        # retrieve the `oauth2_provider.models.OAuth2AccessToken` instance from the access_token
        auth_backend = oauth2_provider_backends.AccessTokenBackend()
        token = auth_backend.authenticate(access_token, client)
        if token is None:
            raise exceptions.AuthenticationFailed("Invalid token")  # does not exist or is expired

        # TODO check scope

        if not self.check_active(token.user):
            raise exceptions.AuthenticationFailed('User not active: %s' % token.user.username)

        if client and token:
            request.user = token.user
            return (request.user, None)

        raise exceptions.AuthenticationFailed(
            'You are not allowed to access this resource.')

    def authenticate_header(self, request):
        """
        Bearer is the only finalized type currently

        Check details on the `OAuth2Authentication.authenticate` method
        """
        return 'Bearer'

    def check_active(self, user):
        """
        Ensures the user has an active account.

        Optimized for the ``django.contrib.auth.models.User`` case.
        """
        if not self.require_active:
            # Ignore & move on.
            return True

        return user.is_active
