"""
Provides various authentication policies.
"""
from __future__ import unicode_literals
import base64

from django.contrib.auth import authenticate
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework.compat import CsrfViewMiddleware
from rest_framework.compat import oauth, oauth_provider, oauth_provider_store
from rest_framework.compat import oauth2_provider, provider_now, check_nonce
from rest_framework.authtoken.models import Token


def get_authorization_header(request):
    """
    Return request's 'Authorization:' header, as a bytestring.

    Hide some test client ickyness where the header can be unicode.
    """
    auth = request.META.get('HTTP_AUTHORIZATION', b'')
    if type(auth) == type(''):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    return auth


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        # Return the failure reason instead of an HttpResponse
        return reason


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
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'basic':
            return None

        if len(auth) == 1:
            msg = 'Invalid basic header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid basic header. Credentials string should not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)

        try:
            auth_parts = base64.b64decode(auth[1]).decode(HTTP_HEADER_ENCODING).partition(':')
        except (TypeError, UnicodeDecodeError):
            msg = 'Invalid basic header. Credentials not correctly base64 encoded'
            raise exceptions.AuthenticationFailed(msg)

        userid, password = auth_parts[0], auth_parts[2]
        return self.authenticate_credentials(userid, password)

    def authenticate_credentials(self, userid, password):
        """
        Authenticate the userid and password against username and password.
        """
        user = authenticate(username=userid, password=password)
        if user is None or not user.is_active:
            raise exceptions.AuthenticationFailed('Invalid username/password')
        return (user, None)

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
        request = request._request
        user = getattr(request, 'user', None)

        # Unauthenticated, CSRF validation not required
        if not user or not user.is_active:
            return None

        self.enforce_csrf(request)

        # CSRF passed with authenticated user
        return (user, None)

    def enforce_csrf(self, request):
        """
        Enforce CSRF validation for session based authentication.
        """
        reason = CSRFCheck().process_view(request, None, (), {})
        if reason:
            # CSRF failed, bail with explicit error message
            raise exceptions.AuthenticationFailed('CSRF Failed: %s' % reason)


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
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'token':
            return None

        if len(auth) == 1:
            msg = 'Invalid token header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid token header. Token string should not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(auth[1])

    def authenticate_credentials(self, key):
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')

        return (token.user, token)

    def authenticate_header(self, request):
        return 'Token'


class OAuthAuthentication(BaseAuthentication):
    """
    OAuth 1.0a authentication backend using `django-oauth-plus` and `oauth2`.

    Note: The `oauth2` package actually provides oauth1.0a support.  Urg.
          We import it from the `compat` module as `oauth`.
    """
    www_authenticate_realm = 'api'

    def __init__(self, *args, **kwargs):
        super(OAuthAuthentication, self).__init__(*args, **kwargs)

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

        if not oauth_request:
            return None

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
        except oauth_provider.store.InvalidConsumerError:
            msg = 'Invalid consumer token: %s' % oauth_request.get_parameter('oauth_consumer_key')
            raise exceptions.AuthenticationFailed(msg)

        if consumer.status != oauth_provider.consts.ACCEPTED:
            msg = 'Invalid consumer key status: %s' % consumer.get_status_display()
            raise exceptions.AuthenticationFailed(msg)

        try:
            token_param = oauth_request.get_parameter('oauth_token')
            token = oauth_provider_store.get_access_token(request, oauth_request, consumer, token_param)
        except oauth_provider.store.InvalidTokenError:
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
        oauth_nonce = oauth_request['oauth_nonce']
        oauth_timestamp = oauth_request['oauth_timestamp']
        return check_nonce(request, oauth_request, oauth_nonce, oauth_timestamp)


class OAuth2Authentication(BaseAuthentication):
    """
    OAuth 2 authentication backend using `django-oauth2-provider`
    """
    www_authenticate_realm = 'api'
    allow_query_params_token = settings.DEBUG

    def __init__(self, *args, **kwargs):
        super(OAuth2Authentication, self).__init__(*args, **kwargs)

        if oauth2_provider is None:
            raise ImproperlyConfigured(
                "The 'django-oauth2-provider' package could not be imported. "
                "It is required for use with the 'OAuth2Authentication' class.")

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """

        auth = get_authorization_header(request).split()

        if auth and auth[0].lower() == b'bearer':
            access_token = auth[1]
        elif 'access_token' in request.POST:
            access_token = request.POST['access_token']
        elif 'access_token' in request.GET and self.allow_query_params_token:
            access_token = request.GET['access_token']
        else:
            return None

        if len(auth) == 1:
            msg = 'Invalid bearer header. No credentials provided.'
            raise exceptions.AuthenticationFailed(msg)
        elif len(auth) > 2:
            msg = 'Invalid bearer header. Token string should not contain spaces.'
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(request, access_token)

    def authenticate_credentials(self, request, access_token):
        """
        Authenticate the request, given the access token.
        """

        try:
            token = oauth2_provider.oauth2.models.AccessToken.objects.select_related('user')
            # provider_now switches to timezone aware datetime when
            # the oauth2_provider version supports to it.
            token = token.get(token=access_token, expires__gt=provider_now())
        except oauth2_provider.oauth2.models.AccessToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        user = token.user

        if not user.is_active:
            msg = 'User inactive or deleted: %s' % user.username
            raise exceptions.AuthenticationFailed(msg)

        return (user, token)

    def authenticate_header(self, request):
        """
        Bearer is the only finalized type currently

        Check details on the `OAuth2Authentication.authenticate` method
        """
        return 'Bearer realm="%s"' % self.www_authenticate_realm
