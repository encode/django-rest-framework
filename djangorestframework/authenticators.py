from django.contrib.auth import authenticate
import base64

class BaseAuthenticator(object):
    """All authenticators should extend BaseAuthenticator."""

    def __init__(self, resource):
        """Initialise the authenticator with the Resource instance as state,
        in case the authenticator needs to access any metadata on the Resource object."""
        self.resource = resource

    def authenticate(self, request):
        """Authenticate the request and return the authentication context or None.

        The default permission checking on Resource will use the allowed_methods attribute
        for permissions if the authentication context is not None, and use anon_allowed_methods otherwise.

        The authentication context is passed to the method calls eg Resource.get(request, auth) in order to
        allow them to apply any more fine grained permission checking at the point the response is being generated.
        
        This function must be overridden to be implemented."""
        return None


class BasicAuthenticator(BaseAuthenticator):
    """Use HTTP Basic authentication"""
    def authenticate(self, request):
        if 'HTTP_AUTHORIZATION' in request.META:
            auth = request.META['HTTP_AUTHORIZATION'].split()
            if len(auth) == 2 and auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    return user
        return None
                

class UserLoggedInAuthenticator(BaseAuthenticator):
    """Use Djagno's built-in request session for authentication."""
    def authenticate(self, request):
        if getattr(request, 'user', None) and request.user.is_active:
            return request.user
        return None
    
