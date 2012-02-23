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
    'UserLoggedInAuthentication'
)


class BaseAuthentication(object):
    """
    All authentication classes should extend BaseAuthentication.
    """

    def __init__(self, view):
        """
        :class:`Authentication` classes are always passed the current view on creation.
        """
        self.view = view

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
    Use HTTP Basic authentication.
    """

    def authenticate(self, request):
        """
        Returns a :obj:`User` if a correct username and password have been supplied
        using HTTP Basic authentication.  Otherwise returns :const:`None`.
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
                    uname, passwd = smart_unicode(auth_parts[0]), smart_unicode(auth_parts[2])
                except DjangoUnicodeDecodeError:
                    return None

                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    return user
        return None


class UserLoggedInAuthentication(BaseAuthentication):
    """
    Use Django's session framework for authentication.
    """

    def authenticate(self, request):
        """
        Returns a :obj:`User` if the request session currently has a logged in user.
        Otherwise returns :const:`None`.
        """
        request.DATA  # Make sure our generic parsing runs first
        user = getattr(request.request, 'user', None)

        if user and user.is_active:
            # Enforce CSRF validation for session based authentication.
            resp = CsrfViewMiddleware().process_view(request, None, (), {})

            if resp is None:  # csrf passed
                return user
        return None


# TODO: TokenAuthentication, DigestAuthentication, OAuthAuthentication
