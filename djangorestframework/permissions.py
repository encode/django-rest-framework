"""
The :mod:`permissions` module bundles a set of  permission classes that are used
for checking if a request passes a certain set of constraints. You can assign a permission
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
    'PerUserThrottling',
    'PerViewThrottling',
    'PerResourceThrottling'
)

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


_403_FORBIDDEN_RESPONSE = ErrorResponse(
    status.HTTP_403_FORBIDDEN,
    {'detail': 'You do not have permission to access this resource. ' +
               'You may need to login or otherwise authenticate the request.'})

_503_SERVICE_UNAVAILABLE = ErrorResponse(
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
        if not user.is_staff:
            raise _403_FORBIDDEN_RESPONSE


class IsUserOrIsAnonReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def check_permission(self, user):
        if (not user.is_authenticated() and
            self.view.method not in SAFE_METHODS):
            raise _403_FORBIDDEN_RESPONSE


class DjangoModelPermissions(BasePermission):
    """
    The request is authenticated using `django.contrib.auth` permissions.
    See: https://docs.djangoproject.com/en/dev/topics/auth/#permissions

    It ensures that the user is authenticated, and has the appropriate
    `add`/`change`/`delete` permissions on the model.

    This permission should only be used on views with a `ModelResource`.
    """

    # Map methods into required permission codes.
    # Override this if you need to also provide 'read' permissions,
    # or if you want to provide custom permission codes.
    perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def get_required_permissions(self, method, model_cls):
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        kwargs = {
            'app_label': model_cls._meta.app_label,
            'model_name':  model_cls._meta.module_name
        }
        try:
            return [perm % kwargs for perm in self.perms_map[method]]
        except KeyError:
            ErrorResponse(status.HTTP_405_METHOD_NOT_ALLOWED)

    def check_permission(self, user):
        method = self.view.method
        model_cls = self.view.resource.model
        perms = self.get_required_permissions(method, model_cls)

        if not user.is_authenticated or not user.has_perms(perms):
            raise _403_FORBIDDEN_RESPONSE


class BaseThrottle(BasePermission):
    """
    Rate throttling of requests.

    The rate (requests / seconds) is set by a :attr:`throttle` attribute
    on the :class:`.View` class.  The attribute is a string of the form 'number of
    requests/period'.

    Period should be one of: ('s', 'sec', 'm', 'min', 'h', 'hour', 'd', 'day')

    Previous request information used for throttling is stored in the cache.
    """

    attr_name = 'throttle'
    default = '0/sec'
    timer = time.time

    def get_cache_key(self):
        """
        Should return a unique cache-key which can be used for throttling.
        Must be overridden.
        """
        pass

    def check_permission(self, auth):
        """
        Check the throttling.
        Return `None` or raise an :exc:`.ErrorResponse`.
        """
        num, period = getattr(self.view, self.attr_name, self.default).split('/')
        self.num_requests = int(num)
        self.duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        self.auth = auth
        self.check_throttle()

    def check_throttle(self):
        """
        Implement the check to see if the request should be throttled.

        On success calls :meth:`throttle_success`.
        On failure calls :meth:`throttle_failure`.
        """
        self.key = self.get_cache_key()
        self.history = cache.get(self.key, [])
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            self.throttle_failure()
        else:
            self.throttle_success()

    def throttle_success(self):
        """
        Inserts the current request's timestamp along with the key
        into the cache.
        """
        self.history.insert(0, self.now)
        cache.set(self.key, self.history, self.duration)
        header = 'status=SUCCESS; next=%s sec' % self.next()
        self.view.add_header('X-Throttle', header)

    def throttle_failure(self):
        """
        Called when a request to the API has failed due to throttling.
        Raises a '503 service unavailable' response.
        """
        header = 'status=FAILURE; next=%s sec' % self.next()
        self.view.add_header('X-Throttle', header)
        raise _503_SERVICE_UNAVAILABLE

    def next(self):
        """
        Returns the recommended next request time in seconds.
        """
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1

        return '%.2f' % (remaining_duration / float(available_requests))


class PerUserThrottling(BaseThrottle):
    """
    Limits the rate of API calls that may be made by a given user.

    The user id will be used as a unique identifier if the user is
    authenticated. For anonymous requests, the IP address of the client will
    be used.
    """

    def get_cache_key(self):
        if self.auth.is_authenticated():
            ident = self.auth.id
        else:
            ident = self.view.request.META.get('REMOTE_ADDR', None)
        return 'throttle_user_%s' % ident


class PerViewThrottling(BaseThrottle):
    """
    Limits the rate of API calls that may be used on a given view.

    The class name of the view is used as a unique identifier to
    throttle against.
    """

    def get_cache_key(self):
        return 'throttle_view_%s' % self.view.__class__.__name__


class PerResourceThrottling(BaseThrottle):
    """
    Limits the rate of API calls that may be used against all views on
    a given resource.

    The class name of the resource is used as a unique identifier to
    throttle against.
    """

    def get_cache_key(self):
        return 'throttle_resource_%s' % self.view.resource.__class__.__name__
