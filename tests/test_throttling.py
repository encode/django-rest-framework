"""
Tests for the throttling implementations in the permissions module.
"""
from __future__ import unicode_literals
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView
from rest_framework.throttling import BaseThrottle, UserRateThrottle, ScopedRateThrottle
from rest_framework.response import Response


class User3SecRateThrottle(UserRateThrottle):
    rate = '3/sec'
    scope = 'seconds'


class User3MinRateThrottle(UserRateThrottle):
    rate = '3/min'
    scope = 'minutes'


class NonTimeThrottle(BaseThrottle):
    def allow_request(self, request, view):
        if not hasattr(self.__class__, 'called'):
            self.__class__.called = True
            return True
        return False 


class MockView(APIView):
    throttle_classes = (User3SecRateThrottle,)

    def get(self, request):
        return Response('foo')


class MockView_MinuteThrottling(APIView):
    throttle_classes = (User3MinRateThrottle,)

    def get(self, request):
        return Response('foo')


class MockView_NonTimeThrottling(APIView):
    throttle_classes = (NonTimeThrottle,)

    def get(self, request):
        return Response('foo')


class ThrottlingTests(TestCase):
    def setUp(self):
        """
        Reset the cache so that no throttles will be active
        """
        cache.clear()
        self.factory = APIRequestFactory()

    def test_requests_are_throttled(self):
        """
        Ensure request rate is limited
        """
        request = self.factory.get('/')
        for dummy in range(4):
            response = MockView.as_view()(request)
        self.assertEqual(429, response.status_code)

    def set_throttle_timer(self, view, value):
        """
        Explicitly set the timer, overriding time.time()
        """
        view.throttle_classes[0].timer = lambda self: value

    def test_request_throttling_expires(self):
        """
        Ensure request rate is limited for a limited duration only
        """
        self.set_throttle_timer(MockView, 0)

        request = self.factory.get('/')
        for dummy in range(4):
            response = MockView.as_view()(request)
        self.assertEqual(429, response.status_code)

        # Advance the timer by one second
        self.set_throttle_timer(MockView, 1)

        response = MockView.as_view()(request)
        self.assertEqual(200, response.status_code)

    def ensure_is_throttled(self, view, expect):
        request = self.factory.get('/')
        request.user = User.objects.create(username='a')
        for dummy in range(3):
            view.as_view()(request)
        request.user = User.objects.create(username='b')
        response = view.as_view()(request)
        self.assertEqual(expect, response.status_code)

    def test_request_throttling_is_per_user(self):
        """
        Ensure request rate is only limited per user, not globally for
        PerUserThrottles
        """
        self.ensure_is_throttled(MockView, 200)

    def ensure_response_header_contains_proper_throttle_field(self, view, expected_headers):
        """
        Ensure the response returns an X-Throttle field with status and next attributes
        set properly.
        """
        request = self.factory.get('/')
        for timer, expect in expected_headers:
            self.set_throttle_timer(view, timer)
            response = view.as_view()(request)
            if expect is not None:
                self.assertEqual(response['X-Throttle-Wait-Seconds'], expect)
            else:
                self.assertFalse('X-Throttle-Wait-Seconds' in response)

    def test_seconds_fields(self):
        """
        Ensure for second based throttles.
        """
        self.ensure_response_header_contains_proper_throttle_field(MockView,
         ((0, None),
          (0, None),
          (0, None),
          (0, '1')
         ))

    def test_minutes_fields(self):
        """
        Ensure for minute based throttles.
        """
        self.ensure_response_header_contains_proper_throttle_field(MockView_MinuteThrottling,
         ((0, None),
          (0, None),
          (0, None),
          (0, '60')
         ))

    def test_next_rate_remains_constant_if_followed(self):
        """
        If a client follows the recommended next request rate,
        the throttling rate should stay constant.
        """
        self.ensure_response_header_contains_proper_throttle_field(MockView_MinuteThrottling,
         ((0, None),
          (20, None),
          (40, None),
          (60, None),
          (80, None)
         ))

    def test_non_time_throttle(self):
        """
        Ensure for second based throttles.
        """
        request = self.factory.get('/')

        self.assertFalse(hasattr(MockView_NonTimeThrottling.throttle_classes[0], 'called'))

        response = MockView_NonTimeThrottling.as_view()(request)
        self.assertFalse('X-Throttle-Wait-Seconds' in response)

        self.assertTrue(MockView_NonTimeThrottling.throttle_classes[0].called)

        response = MockView_NonTimeThrottling.as_view()(request)
        self.assertFalse('X-Throttle-Wait-Seconds' in response) 


class ScopedRateThrottleTests(TestCase):
    """
    Tests for ScopedRateThrottle.
    """

    def setUp(self):
        class XYScopedRateThrottle(ScopedRateThrottle):
            TIMER_SECONDS = 0
            THROTTLE_RATES = {'x': '3/min', 'y': '1/min'}
            timer = lambda self: self.TIMER_SECONDS

        class XView(APIView):
            throttle_classes = (XYScopedRateThrottle,)
            throttle_scope = 'x'

            def get(self, request):
                return Response('x')

        class YView(APIView):
            throttle_classes = (XYScopedRateThrottle,)
            throttle_scope = 'y'

            def get(self, request):
                return Response('y')

        class UnscopedView(APIView):
            throttle_classes = (XYScopedRateThrottle,)

            def get(self, request):
                return Response('y')

        self.throttle_class = XYScopedRateThrottle
        self.factory = APIRequestFactory()
        self.x_view = XView.as_view()
        self.y_view = YView.as_view()
        self.unscoped_view = UnscopedView.as_view()

    def increment_timer(self, seconds=1):
        self.throttle_class.TIMER_SECONDS += seconds

    def test_scoped_rate_throttle(self):
        request = self.factory.get('/')

        # Should be able to hit x view 3 times per minute.
        response = self.x_view(request)
        self.assertEqual(200, response.status_code)

        self.increment_timer()
        response = self.x_view(request)
        self.assertEqual(200, response.status_code)

        self.increment_timer()
        response = self.x_view(request)
        self.assertEqual(200, response.status_code)

        self.increment_timer()
        response = self.x_view(request)
        self.assertEqual(429, response.status_code)

        # Should be able to hit y view 1 time per minute.
        self.increment_timer()
        response = self.y_view(request)
        self.assertEqual(200, response.status_code)

        self.increment_timer()
        response = self.y_view(request)
        self.assertEqual(429, response.status_code)

        # Ensure throttles properly reset by advancing the rest of the minute
        self.increment_timer(55)

        # Should still be able to hit x view 3 times per minute.
        response = self.x_view(request)
        self.assertEqual(200, response.status_code)

        self.increment_timer()
        response = self.x_view(request)
        self.assertEqual(200, response.status_code)

        self.increment_timer()
        response = self.x_view(request)
        self.assertEqual(200, response.status_code)

        self.increment_timer()
        response = self.x_view(request)
        self.assertEqual(429, response.status_code)

        # Should still be able to hit y view 1 time per minute.
        self.increment_timer()
        response = self.y_view(request)
        self.assertEqual(200, response.status_code)

        self.increment_timer()
        response = self.y_view(request)
        self.assertEqual(429, response.status_code)

    def test_unscoped_view_not_throttled(self):
        request = self.factory.get('/')

        for idx in range(10):
            self.increment_timer()
            response = self.unscoped_view(request)
            self.assertEqual(200, response.status_code)
