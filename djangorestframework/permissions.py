from django.core.cache import cache
from djangorestframework import status
import time


class BasePermission(object):
    """A base class from which all permission classes should inherit."""
    def __init__(self, view):
        self.view = view
    
    def has_permission(self, auth):
        return True


class FullAnonAccess(BasePermission):
    """"""
    def has_permission(self, auth):
        return True

class IsAuthenticated(BasePermission):
    """"""
    def has_permission(self, auth):
        return auth is not None and auth.is_authenticated()

#class IsUser(BasePermission):
#    """The request has authenticated as a user."""
#    def has_permission(self, auth):
#        pass
#
#class IsAdminUser():
#    """The request has authenticated as an admin user."""
#    def has_permission(self, auth):
#        pass
#
#class IsUserOrIsAnonReadOnly(BasePermission):
#    """The request has authenticated as a user, or is a read-only request."""
#    def has_permission(self, auth):
#        pass
#
#class OAuthTokenInScope(BasePermission):
#    def has_permission(self, auth):
#        pass
#
#class UserHasModelPermissions(BasePermission):
#    def has_permission(self, auth):
#        pass
    

class Throttling(BasePermission):
    """Rate throttling of requests on a per-user basis.

    The rate is set by a 'throttle' attribute on the view class.
    The attribute is a two tuple of the form (number of requests, duration in seconds).

    The user's id will be used as a unique identifier if the user is authenticated.
    For anonymous requests, the IP address of the client will be used.

    Previous request information used for throttling is stored in the cache.
    """
    def has_permission(self, auth):
        (num_requests, duration) = getattr(self.view, 'throttle', (0, 0))

        if auth.is_authenticated():
            ident = str(auth)
        else:
            ident = self.view.request.META.get('REMOTE_ADDR', None)

        key = 'throttle_%s' % ident
        history = cache.get(key, [])
        now = time.time()
        
        # Drop any requests from the history which have now passed the throttle duration
        while history and history[0] < now - duration:
            history.pop()

        if len(history) >= num_requests:
            raise ErrorResponse(status.HTTP_503_SERVICE_UNAVAILABLE, {'detail': 'request was throttled'})

        history.insert(0, now)
        cache.set(key, history, duration)        
