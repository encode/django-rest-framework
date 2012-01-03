"""
The :mod:`authentication` module provides a set of pluggable authentication
classes.

Authentication behavior is provided by mixing the :class:`mixins.AuthMixin`
class into a :class:`View` class.

The set of authentication methods which are used is then specified by setting
the :attr:`authentication` attribute on the :class:`View` class, and listing a
set of :class:`authentication` classes.
"""

from django.contrib.auth import authenticate
from djangorestframework.compat import CsrfViewMiddleware
from djangorestframework.utils import as_tuple
import base64

__all__ = (
    'BaseAuthentication',
    'BasicAuthentication',
    'UserLoggedInAuthentication'
)


class BaseAuthentication(object):
    """
    All authentication classes should extend BaseAuthentication.
    """

    def __init__(self, view):
        """
        :class:`Authentication` classes are always passed the current view on
        creation.
        """
        self.view = view

    def authenticate(self, request):
        """
        Authenticate the :obj:`request` and return a :obj:`User` or
        :const:`None`. [*]_

        .. [*] The authentication context *will* typically be a :obj:`User`,
            but it need not be.  It can be any user-like object so long as the
            permissions classes (see the :mod:`permissions` module) on the view
            can handle the object and use it to determine if the request has
            the required permissions or not.

            This can be an important distinction if you're implementing some
            token based authentication mechanism, where the authentication
            context may be more involved than simply mapping to a :obj:`User`.
        """
        return None


class BasicAuthentication(BaseAuthentication):
    """
    Use HTTP Basic authentication.
    """
    def _authenticate_user(self, username, password):
        user = authenticate(username=username, password=password)
        if user and user.is_active:
            return user
        return None

    def authenticate(self, request):
        """
        Returns a :obj:`User` if a correct username and password have been
        supplied using HTTP Basic authentication.
        Otherwise returns :const:`None`.
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
                    username = smart_unicode(auth_parts[0])
                    password = smart_unicode(auth_parts[2])
                except DjangoUnicodeDecodeError:
                    return None

                user = authenticate(username=username, password=password)
                if user is not None and user.is_active:
                    return user
        return None


class UserLoggedInAuthentication(BaseAuthentication):
    """
    Use Django's session framework for authentication.
    """

    def authenticate(self, request):
        """
        Returns a :obj:`User` if the request session currently has a logged in
        user. Otherwise returns :const:`None`.
        """
        # TODO: Might be cleaner to switch this back to using request.POST,
        #       and let FormParser/MultiPartParser deal with the consequences.
        if getattr(request, 'user', None) and request.user.is_active:
            # Enforce CSRF validation for session based authentication.

            # Temporarily replace request.POST with .DATA, to use our generic parsing.
            # If DATA is not dict-like, use an empty dict.
            if request.method.upper() == 'POST':
                if hasattr(self.view.DATA, 'get'):
                    request._post = self.view.DATA
                else:
                    request._post = {}

            resp = CsrfViewMiddleware().process_view(request, None, (), {})

            # Replace request.POST
            if request.method.upper() == 'POST':
                del(request._post)

            if resp is None:  # csrf passed
                return request.user
        return None


# TODO: TokenAuthentication, DigestAuthentication, OAuthAuthentication
