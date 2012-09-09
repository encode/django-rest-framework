"""
The :mod:`authentication` module provides a set of pluggable authentication classes.

Authentication behavior is provided by mixing the :class:`mixins.RequestMixin` class into a :class:`View` class.
"""

from django.contrib.auth import authenticate
from djangorestframework.compat import CsrfViewMiddleware
import base64

__all__ = (
    'BaseAuthentication',
    'BasicAuthentication',
    'SessionAuthentication'
)


class BaseAuthentication(object):
    """
    All authentication classes should extend BaseAuthentication.
    """

    def authenticate(self, request):
        """
        Authenticate the :obj:`request` and return a :obj:`User` or :const:`None`. [*]_

        .. [*] The authentication context *will* typically be a :obj:`User`,
            but it need not be.  It can be any user-like object so long as the
            permissions classes (see the :mod:`permissions` module) on the view can
            handle the object and use it to determine if the request has the required
            permissions or not.

            This can be an important distinction if you're implementing some token
            based authentication mechanism, where the authentication context
            may be more involved than simply mapping to a :obj:`User`.
        """
        return None


class BasicAuthentication(BaseAuthentication):
    """
    Base class for HTTP Basic authentication.
    Subclasses should implement `.authenticate_credentials()`.
    """

    def authenticate(self, request):
        """
        Returns a `User` if a correct username and password have been supplied
        using HTTP Basic authentication.  Otherwise returns `None`.
        """
        from django.utils.encoding import smart_unicode, DjangoUnicodeDecodeError

        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2 and auth[0].lower() == "basic":
                try:
                    auth_parts = base64.b64decode(auth[1]).partition(':')
                except TypeError:
                    return None

                try:
                    userid, password = smart_unicode(auth_parts[0]), smart_unicode(auth_parts[2])
                except DjangoUnicodeDecodeError:
                    return None

                return self.authenticate_credentials(userid, password)

    def authenticate_credentials(self, userid, password):
        """
        Given the Basic authentication userid and password, authenticate
        and return a user instance.
        """
        raise NotImplementedError('.authenticate_credentials() must be overridden')


class UserBasicAuthentication(BasicAuthentication):
    def authenticate_credentials(self, userid, password):
        """
        Authenticate the userid and password against username and password.
        """
        user = authenticate(username=userid, password=password)
        if user is not None and user.is_active:
            return (user, None)


class SessionAuthentication(BaseAuthentication):
    """
    Use Django's session framework for authentication.
    """

    def authenticate(self, request):
        """
        Returns a :obj:`User` if the request session currently has a logged in user.
        Otherwise returns :const:`None`.
        """
        user = getattr(request._request, 'user', None)

        if user and user.is_active:
            # Enforce CSRF validation for session based authentication.
            resp = CsrfViewMiddleware().process_view(request, None, (), {})

            if resp is None:  # csrf passed
                return (user, None)


class TokenAuthentication(BaseAuthentication):
    """
    Use a token model for authentication.

    A custom token model may be used here, but must have the following minimum
    properties:

    * key -- The string identifying the token
    * user -- The user to which the token belongs
    * revoked -- The status of the token

    The token key should be passed in as a string to the "Authorization" HTTP
    header.  For example:

        Authorization: 0123456789abcdef0123456789abcdef

    """
    model = None

    def authenticate(self, request):
        key = request.META.get('HTTP_AUTHORIZATION', '').strip()

        if self.model is None:
            from djangorestframework.tokenauth.models import BasicToken
            self.model = BasicToken

        try:
             token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
             return None

        if token.user.is_active and not token.revoked:
            return (token.user, token)

# TODO: DigestAuthentication, OAuthAuthentication
