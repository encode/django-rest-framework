from django.core.cache import cache
from djangorestframework.settings import api_settings
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

    def allow_request(self, request):
        """
        Return `True` if the request should be allowed, `False` otherwise.
        """
        raise NotImplementedError('.allow_request() must be overridden')

    def wait(self):
        """
        Optionally, return a recommeded number of seconds to wait before
        the next request.
        """
        return None


class SimpleRateThottle(BaseThrottle):
    """
    A simple cache implementation, that only requires `.get_cache_key()`
    to be overridden.

    The rate (requests / seconds) is set by a :attr:`throttle` attribute
    on the :class:`.View` class.  The attribute is a string of the form 'number of
    requests/period'.

    Period should be one of: ('s', 'sec', 'm', 'min', 'h', 'hour', 'd', 'day')

    Previous request information used for throttling is stored in the cache.
    """

    timer = time.time
    settings = api_settings
    cache_format = '%(class)s_%(scope)s_%(ident)s'
    scope = None

    def __init__(self, view):
        super(SimpleRateThottle, self).__init__(view)
        rate = self.get_rate_description()
        self.num_requests, self.duration = self.parse_rate_description(rate)

    def get_cache_key(self, request):
        """
        Should return a unique cache-key which can be used for throttling.
        Must be overridden.

        May return `None` if the request should not be throttled.
        """
        raise NotImplementedError('.get_cache_key() must be overridden')

    def get_rate_description(self):
        """
        Determine the string representation of the allowed request rate.
        """
        try:
            return self.rate
        except AttributeError:
            return self.settings.DEFAULT_THROTTLE_RATES.get(self.scope)

    def parse_rate_description(self, rate):
        """
        Given the request rate string, return a two tuple of:
        <allowed number of requests>, <period of time in seconds>
        """
        assert rate, "No throttle rate set for '%s'" % self.__class__.__name__
        num, period = rate.split('/')
        num_requests = int(num)
        duration = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}[period[0]]
        return (num_requests, duration)

    def allow_request(self, request):
        """
        Implement the check to see if the request should be throttled.

        On success calls `throttle_success`.
        On failure calls `throttle_failure`.
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


class AnonRateThrottle(SimpleRateThottle):
    """
    Limits the rate of API calls that may be made by a anonymous users.

    The IP address of the request will be used as the unqiue cache key.
    """
    scope = 'anon'

    def get_cache_key(self, request):
        if request.user.is_authenticated():
            return None  # Only throttle unauthenticated requests.

        ident = request.META.get('REMOTE_ADDR', None)

        return self.cache_format % {
            'class': self.__class__.__name__,
            'scope': self.scope,
            'ident': ident
        }


class UserRateThrottle(SimpleRateThottle):
    """
    Limits the rate of API calls that may be made by a given user.

    The user id will be used as a unique cache key if the user is
    authenticated.  For anonymous requests, the IP address of the request will
    be used.
    """
    scope = 'user'

    def get_cache_key(self, request):
        if request.user.is_authenticated():
            ident = request.user.id
        else:
            ident = request.META.get('REMOTE_ADDR', None)

        return self.cache_format % {
            'class': self.__class__.__name__,
            'scope': self.scope,
            'ident': ident
        }


class ScopedRateThrottle(SimpleRateThottle):
    """
    Limits the rate of API calls by different amounts for various parts of
    the API.  Any view that has the `throttle_scope` property set will be
    throttled.  The unique cache key will be generated by concatenating the
    user id of the request, and the scope of the view being accessed.
    """

    def __init__(self, view):
        """
        Scope is determined from the view being accessed.
        """
        self.scope = getattr(self.view, 'throttle_scope', None)
        super(ScopedRateThrottle, self).__init__(view)

    def parse_rate_description(self, rate):
        """
        Subclassed so that we don't fail if `view.throttle_scope` is not set.
        """
        if not rate:
            return (None, None)
        return super(ScopedRateThrottle, self).parse_rate_description(rate)

    def get_cache_key(self, request):
        """
        If `view.throttle_scope` is not set, don't apply this throttle.

        Otherwise generate the unique cache key by concatenating the user id
        with the '.throttle_scope` property of the view.
        """
        if not self.scope:
            return None  # Only throttle views with `.throttle_scope` set.

        if request.user.is_authenticated():
            ident = request.user.id
        else:
            ident = request.META.get('REMOTE_ADDR', None)

        return self.cache_format % {
            'class': self.__class__.__name__,
            'scope': self.scope,
            'ident': ident
        }
