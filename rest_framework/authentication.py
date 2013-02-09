"""
Provides a set of pluggable authentication policies.
"""
from __future__ import unicode_literals
from django.contrib.auth import authenticate
from django.utils.encoding import DjangoUnicodeDecodeError
from rest_framework import exceptions, HTTP_HEADER_ENCODING
from rest_framework.compat import CsrfViewMiddleware
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


# TODO: OAuthAuthentication
