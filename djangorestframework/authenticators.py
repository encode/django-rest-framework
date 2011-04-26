"""The :mod:`authenticators` modules provides for pluggable authentication behaviour.

Authentication behaviour is provided by adding the mixin class :class:`AuthenticatorMixin` to a :class:`.Resource` or Django :class:`View` class.

The set of authenticators which are use is then specified by setting the :attr:`authenticators` attribute on the class, and listing a set of authenticator classes.
"""
from django.contrib.auth import authenticate
from django.middleware.csrf import CsrfViewMiddleware
from djangorestframework.utils import as_tuple
import base64


class AuthenticatorMixin(object):
    """Adds pluggable authentication behaviour."""
    
    """The set of authenticators to use."""
    authenticators = None

    def authenticate(self, request):
        """Attempt to authenticate the request, returning an authentication context or None.
        An authentication context may be any object, although in many cases it will simply be a :class:`User` instance."""
        
        # Attempt authentication against each authenticator in turn,
        # and return None if no authenticators succeed in authenticating the request.
        for authenticator in as_tuple(self.authenticators):
            auth_context = authenticator(self).authenticate(request)
            if auth_context:
                return auth_context

        return None


class BaseAuthenticator(object):
    """All authenticators should extend BaseAuthenticator."""

    def __init__(self, mixin):
        """Initialise the authenticator with the mixin instance as state,
        in case the authenticator needs to access any metadata on the mixin object."""
        self.mixin = mixin

    def authenticate(self, request):
        """Authenticate the request and return the authentication context or None.

        An authentication context might be something as simple as a User object, or it might
        be some more complicated token, for example authentication tokens which are signed
        against a particular set of permissions for a given user, over a given timeframe.

        The default permission checking on Resource will use the allowed_methods attribute
        for permissions if the authentication context is not None, and use anon_allowed_methods otherwise.

        The authentication context is passed to the method calls eg Resource.get(request, auth) in order to
        allow them to apply any more fine grained permission checking at the point the response is being generated.
        
        This function must be overridden to be implemented."""
        return None


class BasicAuthenticator(BaseAuthenticator):
    """Use HTTP Basic authentication"""
    def authenticate(self, request):
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
                

class UserLoggedInAuthenticator(BaseAuthenticator):
    """Use Django's built-in request session for authentication."""
    def authenticate(self, request):
        if getattr(request, 'user', None) and request.user.is_active:
            # If this is a POST request we enforce CSRF validation.
            if request.method.upper() == 'POST':
                # Temporarily replace request.POST with .RAW_CONTENT,
                # so that we use our more generic request parsing
                request._post = self.mixin.RAW_CONTENT
                resp = CsrfViewMiddleware().process_view(request, None, (), {})
                del(request._post)
                if resp is not None:  # csrf failed
                    return None
            return request.user
        return None
    
