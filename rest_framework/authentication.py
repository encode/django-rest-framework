"""
Provides a set of pluggable authentication policies.
"""
from __future__ import unicode_literals
from django.contrib.auth import authenticate
from django.utils.encoding import DjangoUnicodeDecodeError
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework.compat import CsrfViewMiddleware
from rest_framework.compat import oauth2_provider
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
        oauth2_client_form = oauth2_provider.forms.ClientAuthForm(request.REQUEST)
        if not oauth2_client_form.is_valid():
            raise exceptions.AuthenticationFailed("Client could not be validated")
        client = oauth2_client_form.cleaned_data.get('client')

        # retrieve the `oauth2_provider.models.OAuth2AccessToken` instance from the access_token
        auth_backend = oauth2_provider.backends.AccessTokenBackend()
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
