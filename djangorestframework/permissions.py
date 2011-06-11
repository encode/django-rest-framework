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


class PerUserThrottling(BasePermission):
    """
    Rate throttling of requests on a per-user basis.

    The rate (requests / seconds) is set by a :attr:`throttle` attribute on the ``View`` class.
    The attribute is a two tuple of the form (number of requests, duration in seconds).

    The user id will be used as a unique identifier if the user is authenticated.
    For anonymous requests, the IP address of the client will be used.

    Previous request information used for throttling is stored in the cache.
    """

    def check_permission(self, user):
        (num_requests, duration) = getattr(self.view, 'throttle', (0, 0))
        
        if user.is_authenticated():
            ident = str(user)
        else:
            ident = self.view.request.META.get('REMOTE_ADDR', None)

        key = 'throttle_%s' % ident
        history = cache.get(key, [])
        now = time.time()
        
        # Drop any requests from the history which have now passed the throttle duration
        while history and history[0] < now - duration:
            history.pop()

        if len(history) >= num_requests:
            raise _503_THROTTLED_RESPONSE

        history.insert(0, now)
        cache.set(key, history, duration)

class PerResourceThrottling(BasePermission):
    """
    Rate throttling of requests on a per-resource basis.

    The rate (requests / seconds) is set by a :attr:`throttle` attribute on the ``View`` class.
    The attribute is a two tuple of the form (number of requests, duration in seconds).

    The user id will be used as a unique identifier if the user is authenticated.
    For anonymous requests, the IP address of the client will be used.

    Previous request information used for throttling is stored in the cache.
    """

    def check_permission(self, ignore):
        (num_requests, duration) = getattr(self.view, 'throttle', (0, 0))
        
        
        key = 'throttle_%s' % self.view.__class__.__name__
        
        history = cache.get(key, [])
        now = time.time()
        
        # Drop any requests from the history which have now passed the throttle duration
        while history and history[0] < now - duration:
            history.pop()

        if len(history) >= num_requests:
            raise _503_THROTTLED_RESPONSE

        history.insert(0, now)
        cache.set(key, history, duration)
