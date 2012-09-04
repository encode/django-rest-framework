from django.core.cache import cache
import time


class BaseThrottle(object):
    """
    Rate throttling of requests.
    """

    def __init__(self, view=None):
        """
        All throttles hold a reference to the instantiating view.
        """
        self.view = view

    def check_throttle(self, request):
        """
        Return `True` if the request should be allowed, `False` otherwise.
        """
        raise NotImplementedError('.check_throttle() must be overridden')

    def wait(self):
        """
        Optionally, return a recommeded number of seconds to wait before
        the next request.
        """
        return None


class SimpleCachingThrottle(BaseThrottle):
    """
    A simple cache implementation, that only requires `.get_cache_key()`
    to be overridden.

    The rate (requests / seconds) is set by a :attr:`throttle` attribute
    on the :class:`.View` class.  The attribute is a string of the form 'number of
    requests/period'.

    Period should be one of: ('s', 'sec', 'm', 'min', 'h', 'hour', 'd', 'day')

    Previous request information used for throttling is stored in the cache.
    """

    attr_name = 'rate'
    rate = '1000/day'
    timer = time.time

    def __init__(self, view):
        """
        Check the throttling.
        Return `None` or raise an :exc:`.ImmediateResponse`.
        """
        super(SimpleCachingThrottle, self).__init__(view)
        num, period = getattr(view, self.attr_name, self.rate).split('/')
        self.num_requests = int(num)
        self.duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]

    def get_cache_key(self, request):
        """
        Should return a unique cache-key which can be used for throttling.
        Must be overridden.
        """
        raise NotImplementedError('.get_cache_key() must be overridden')

    def check_throttle(self, request):
        """
        Implement the check to see if the request should be throttled.

        On success calls :meth:`throttle_success`.
        On failure calls :meth:`throttle_failure`.
        """
        self.key = self.get_cache_key(request)
        self.history = cache.get(self.key, [])
        self.now = self.timer()

        # Drop any requests from the history which have now passed the
        # throttle duration
        while self.history and self.history[-1] <= self.now - self.duration:
            self.history.pop()
        if len(self.history) >= self.num_requests:
            return self.throttle_failure()
        return self.throttle_success()

    def throttle_success(self):
        """
        Inserts the current request's timestamp along with the key
        into the cache.
        """
        self.history.insert(0, self.now)
        cache.set(self.key, self.history, self.duration)
        return True

    def throttle_failure(self):
        """
        Called when a request to the API has failed due to throttling.
        """
        return False

    def wait(self):
        """
        Returns the recommended next request time in seconds.
        """
        if self.history:
            remaining_duration = self.duration - (self.now - self.history[-1])
        else:
            remaining_duration = self.duration

        available_requests = self.num_requests - len(self.history) + 1

        return remaining_duration / float(available_requests)


class PerUserThrottling(SimpleCachingThrottle):
    """
    Limits the rate of API calls that may be made by a given user.

    The user id will be used as a unique identifier if the user is
    authenticated. For anonymous requests, the IP address of the client will
    be used.
    """

    def get_cache_key(self, request):
        if request.user.is_authenticated():
            ident = request.user.id
        else:
            ident = request.META.get('REMOTE_ADDR', None)
        return 'throttle_user_%s' % ident


class PerViewThrottling(SimpleCachingThrottle):
    """
    Limits the rate of API calls that may be used on a given view.

    The class name of the view is used as a unique identifier to
    throttle against.
    """

    def get_cache_key(self, request):
        return 'throttle_view_%s' % self.view.__class__.__name__
