"""
Provides a set of pluggable authentication policies.
"""
from __future__ import unicode_literals
from django.contrib.auth import authenticate
from django.utils.encoding import DjangoUnicodeDecodeError
from django.core.exceptions import ImproperlyConfigured
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework.compat import CsrfViewMiddleware
from rest_framework.compat import oauth
from rest_framework.compat import oauth_provider
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

        try:
            userid, password = auth_parts[0], auth_parts[2]
        except DjangoUnicodeDecodeError:
            raise exceptions.AuthenticationFailed('Invalid basic header')

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
    """rest_framework OAuth authentication backend using
    django-oath-plus and oauth2"""
    www_authenticate_realm = 'api'
    require_active = True

    def __init__(self, **kwargs):
        super(OAuthAuthentication, self).__init__(**kwargs)

        if oauth is None:
            raise ImproperlyConfigured("The 'oauth2' package could not be imported. It is required for use with the 'OAuthAuthentication' class.")

        if oauth_provider is None:
            raise ImproperlyConfigured("The 'django-oauth-plus' package could not be imported. It is required for use with the 'OAuthAuthentication' class.")


    def authenticate(self, request):
        """
        Returns two-tuple of (user, auth token) if authentication succeeds, or None otherwise.
        """
        from oauth_provider.store import store
        if self.is_valid_request(request):
            oauth_request = oauth_provider.utils.get_oauth_request(request)

            if not self.check_nonce(request, oauth_request):
                raise exceptions.AuthenticationFailed("Nonce check failed")

            try:
                consumer = store.get_consumer(request, oauth_request,
                    oauth_request.get_parameter('oauth_consumer_key'))
            except oauth_provider.store.InvalidConsumerError, e:
                raise exceptions.AuthenticationFailed(e)

            if consumer.status != oauth_provider.consts.ACCEPTED:
                raise exceptions.AuthenticationFailed('Invalid consumer key status: %s' % consumer.get_status_display())

            try:
                token = store.get_access_token(request, oauth_request,
                    consumer, oauth_request.get_parameter('oauth_token'))

            except oauth_provider.store.InvalidTokenError:
                raise exceptions.AuthenticationFailed(
                    'Invalid access token: %s' % oauth_request.get_parameter('oauth_token'))

            try:
                self.validate_token(request, consumer, token)
            except oauth.Error, e:
                raise exceptions.AuthenticationFailed(e.message)

            if not self.check_active(token.user):
                raise exceptions.AuthenticationFailed('User not active: %s' % token.user.username)

            if consumer and token:
                return (token.user, token)

            raise exceptions.AuthenticationFailed(
                'You are not allowed to access this resource.')

        return None

    def authenticate_header(self, request):
        return 'OAuth realm="%s"' % self.www_authenticate_realm

    def is_in(self, params):
        """
        Checks to ensure that all the OAuth parameter names are in the
        provided ``params``.
        """
        from oauth_provider.consts import OAUTH_PARAMETERS_NAMES

        for param_name in OAUTH_PARAMETERS_NAMES:
            if param_name not in params:
                return False

        return True

    def is_valid_request(self, request):
        """
        Checks whether the required parameters are either in the HTTP
        ``Authorization`` header sent by some clients (the preferred method
        according to OAuth spec) or fall back to ``GET/POST``.
        """
        auth_params = request.META.get("HTTP_AUTHORIZATION", [])
        return self.is_in(auth_params) or self.is_in(request.REQUEST)

    def validate_token(self, request, consumer, token):
        oauth_server, oauth_request = oauth_provider.utils.initialize_server_request(request)
        return oauth_server.verify_request(oauth_request, consumer, token)

    def check_active(self, user):
        """
        Ensures the user has an active account.

        Optimized for the ``django.contrib.auth.models.User`` case.
        """
        if not self.require_active:
            # Ignore & move on.
            return True

        return user.is_active

    def check_nonce(self, request, oauth_request):
        """Checks nonce of request"""
        return oauth_provider.store.store.check_nonce(request, oauth_request, oauth_request['oauth_nonce'])
