"""
The :mod:`permissions` module bundles a set of  permission classes that are used 
for checking if a request passes a certain set of constraints. You can assign a permision 
class to your view by setting your View's :attr:`permissions` class attribute.
"""

from django.core.cache import cache
from djangorestframework import status
from djangorestframework.response import ErrorResponse
import time

__all__ = (
    'BasePermission',
    'FullAnonAccess',
    'IsAuthenticated',
    'IsAdminUser',
    'IsUserOrIsAnonReadOnly',
    'PerUserThrottling'
)


_403_FORBIDDEN_RESPONSE = ErrorResponse(
    status.HTTP_403_FORBIDDEN,
    {'detail': 'You do not have permission to access this resource. ' +
               'You may need to login or otherwise authenticate the request.'})

_503_THROTTLED_RESPONSE = ErrorResponse(
    status.HTTP_503_SERVICE_UNAVAILABLE,
    {'detail': 'request was throttled'})


class ConfigurationException(BaseException):
        """To alert for bad configuration desicions as a convenience."""
        pass


class BasePermission(object):
    """
    A base class from which all permission classes should inherit.
    """
    def __init__(self, view):
        """
        Permission classes are always passed the current view on creation.
        """
        self.view = view
    
    def check_permission(self, auth):
        """
        Should simply return, or raise an :exc:`response.ErrorResponse`.
        """
        pass


class FullAnonAccess(BasePermission):
    """
    Allows full access.
    """

    def check_permission(self, user):
        pass


class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def check_permission(self, user):
        if not user.is_authenticated():
            raise _403_FORBIDDEN_RESPONSE 


class IsAdminUser(BasePermission):
    """
    Allows access only to admin users.
    """

    def check_permission(self, user):
        if not user.is_admin():
            raise _403_FORBIDDEN_RESPONSE


class IsUserOrIsAnonReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def check_permission(self, user): 
        if (not user.is_authenticated() and
            self.view.method != 'GET' and
            self.view.method != 'HEAD'):
            raise _403_FORBIDDEN_RESPONSE

class BaseThrottle(BasePermission):
    """
    Rate throttling of requests.

    The rate (requests / seconds) is set by a :attr:`throttle` attribute on the ``View`` class.
    The attribute is a string of the form 'number of requests/period'. Period must be an element
    of (sec, min, hour, day)

    Previous request information used for throttling is stored in the cache.
    """    

    def get_cache_key(self):
        """Should return the cache-key corresponding to the semantics of the class that implements
        the throttling behaviour. 
        """
        pass

    def check_permission(self, auth):
        num, period = getattr(self.view, 'throttle', '0/sec').split('/')
        self.num_requests = int(num)
        self.duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        self.auth = auth
        self.check_throttle()
        
    def check_throttle(self):
        """On success calls `throttle_success`. On failure calls `throttle_failure`. """
        self.key = self.get_cache_key()
        self.history = cache.get(self.key, [])
        self.now = time.time()
        
        # Drop any requests from the history which have now passed the throttle duration
        while self.history and self.history[0] < self.now - self.duration:
            self.history.pop()

        if len(self.history) >= self.num_requests:
            self.throttle_failure()
        else:
            self.throttle_success()
    
    def throttle_success(self):
        """Inserts the current request's timesatmp along with the key into the cache."""
        self.history.insert(0, self.now)
        cache.set(self.key, self.history, self.duration)
    
    def throttle_failure(self):
        """Raises a 503 """
        raise _503_THROTTLED_RESPONSE
    
class PerUserThrottling(BaseThrottle):
    """
    The user id will be used as a unique identifier if the user is authenticated.
    For anonymous requests, the IP address of the client will be used.
    """

    def get_cache_key(self):
        if self.auth.is_authenticated():
            ident = str(self.auth)
        else:
            ident = self.view.request.META.get('REMOTE_ADDR', None)
        return 'throttle_%s' % ident

class PerViewThrottling(BaseThrottle):
    """
    The class name of the cuurent view will be used as a unique identifier.
    """

    def get_cache_key(self):
        return 'throttle_%s' % self.view.__class__.__name__
    
class PerResourceThrottling(BaseThrottle):
    """
    The class name of the cuurent resource will be used as a unique identifier.
    Raises :exc:`ConfigurationException` if no resource attribute is set on the view class.
    """

    def get_cache_key(self):
        if self.view.resource != None:
            return 'throttle_%s' % self.view.resource.__class__.__name__
        raise ConfigurationException(
            "A per-resource throttle was set to a view that does not have a resource.")