"""
Tests for the throttling implementations in the permissions module.
"""
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework.throttling import (
    BaseThrottle, ScopedRateThrottle, SimpleRateThrottle, UserRateThrottle
)
from rest_framework.views import APIView


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
        assert response.status_code == 429

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
        assert response.status_code == 429

        # Advance the timer by one second
        self.set_throttle_timer(MockView, 1)

        response = MockView.as_view()(request)
        assert response.status_code == 200

    def ensure_is_throttled(self, view, expect):
        request = self.factory.get('/')
        request.user = User.objects.create(username='a')
        for dummy in range(3):
            view.as_view()(request)
        request.user = User.objects.create(username='b')
        response = view.as_view()(request)
        assert response.status_code == expect

    def test_request_throttling_is_per_user(self):
        """
        Ensure request rate is only limited per user, not globally for
        PerUserThrottles
        """
        self.ensure_is_throttled(MockView, 200)

    def ensure_response_header_contains_proper_throttle_field(self, view, expected_headers):
        """
        Ensure the response returns an Retry-After field with status and next attributes
        set properly.
        """
        request = self.factory.get('/')
        for timer, expect in expected_headers:
            self.set_throttle_timer(view, timer)
            response = view.as_view()(request)
            if expect is not None:
                assert response['Retry-After'] == expect
            else:
                assert not'Retry-After' in response

    def test_seconds_fields(self):
        """
        Ensure for second based throttles.
        """
        self.ensure_response_header_contains_proper_throttle_field(
            MockView, (
                (0, None),
                (0, None),
                (0, None),
                (0, '1')
            )
        )

    def test_minutes_fields(self):
        """
        Ensure for minute based throttles.
        """
        self.ensure_response_header_contains_proper_throttle_field(
            MockView_MinuteThrottling, (
                (0, None),
                (0, None),
                (0, None),
                (0, '60')
            )
        )

    def test_next_rate_remains_constant_if_followed(self):
        """
        If a client follows the recommended next request rate,
        the throttling rate should stay constant.
        """
        self.ensure_response_header_contains_proper_throttle_field(
            MockView_MinuteThrottling, (
                (0, None),
                (20, None),
                (40, None),
                (60, None),
                (80, None)
            )
        )

    def test_non_time_throttle(self):
        """
        Ensure for second based throttles.
        """
        request = self.factory.get('/')

        self.assertFalse(hasattr(MockView_NonTimeThrottling.throttle_classes[0], 'called'))

        response = MockView_NonTimeThrottling.as_view()(request)
        self.assertFalse('Retry-After' in response)

        self.assertTrue(MockView_NonTimeThrottling.throttle_classes[0].called)

        response = MockView_NonTimeThrottling.as_view()(request)
        self.assertFalse('Retry-After' in response)


class ScopedRateThrottleTests(TestCase):
    """
    Tests for ScopedRateThrottle.
    """

    def setUp(self):
        class XYScopedRateThrottle(ScopedRateThrottle):
            TIMER_SECONDS = 0
            THROTTLE_RATES = {'x': '3/min', 'y': '1/min'}

            def timer(self):
                return self.TIMER_SECONDS

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
        assert response.status_code == 200

        self.increment_timer()
        response = self.x_view(request)
        assert response.status_code == 200

        self.increment_timer()
        response = self.x_view(request)
        assert response.status_code == 200
        self.increment_timer()
        response = self.x_view(request)
        assert response.status_code == 429

        # Should be able to hit y view 1 time per minute.
        self.increment_timer()
        response = self.y_view(request)
        assert response.status_code == 200

        self.increment_timer()
        response = self.y_view(request)
        assert response.status_code == 429

        # Ensure throttles properly reset by advancing the rest of the minute
        self.increment_timer(55)

        # Should still be able to hit x view 3 times per minute.
        response = self.x_view(request)
        assert response.status_code == 200

        self.increment_timer()
        response = self.x_view(request)
        assert response.status_code == 200

        self.increment_timer()
        response = self.x_view(request)
        assert response.status_code == 200

        self.increment_timer()
        response = self.x_view(request)
        assert response.status_code == 429

        # Should still be able to hit y view 1 time per minute.
        self.increment_timer()
        response = self.y_view(request)
        assert response.status_code == 200

        self.increment_timer()
        response = self.y_view(request)
        assert response.status_code == 429

    def test_unscoped_view_not_throttled(self):
        request = self.factory.get('/')

        for idx in range(10):
            self.increment_timer()
            response = self.unscoped_view(request)
            assert response.status_code == 200


class XffTestingBase(TestCase):
    def setUp(self):

        class Throttle(ScopedRateThrottle):
            THROTTLE_RATES = {'test_limit': '1/day'}
            TIMER_SECONDS = 0

            def timer(self):
                return self.TIMER_SECONDS

        class View(APIView):
            throttle_classes = (Throttle,)
            throttle_scope = 'test_limit'

            def get(self, request):
                return Response('test_limit')

        cache.clear()
        self.throttle = Throttle()
        self.view = View.as_view()
        self.request = APIRequestFactory().get('/some_uri')
        self.request.META['REMOTE_ADDR'] = '3.3.3.3'
        self.request.META['HTTP_X_FORWARDED_FOR'] = '0.0.0.0, 1.1.1.1, 2.2.2.2'

    def config_proxy(self, num_proxies):
        setattr(api_settings, 'NUM_PROXIES', num_proxies)


class IdWithXffBasicTests(XffTestingBase):
    def test_accepts_request_under_limit(self):
        self.config_proxy(0)
        assert self.view(self.request).status_code == 200

    def test_denies_request_over_limit(self):
        self.config_proxy(0)
        self.view(self.request)
        assert self.view(self.request).status_code == 429


class XffSpoofingTests(XffTestingBase):
    def test_xff_spoofing_doesnt_change_machine_id_with_one_app_proxy(self):
        self.config_proxy(1)
        self.view(self.request)
        self.request.META['HTTP_X_FORWARDED_FOR'] = '4.4.4.4, 5.5.5.5, 2.2.2.2'
        assert self.view(self.request).status_code == 429

    def test_xff_spoofing_doesnt_change_machine_id_with_two_app_proxies(self):
        self.config_proxy(2)
        self.view(self.request)
        self.request.META['HTTP_X_FORWARDED_FOR'] = '4.4.4.4, 1.1.1.1, 2.2.2.2'
        assert self.view(self.request).status_code == 429


class XffUniqueMachinesTest(XffTestingBase):
    def test_unique_clients_are_counted_independently_with_one_proxy(self):
        self.config_proxy(1)
        self.view(self.request)
        self.request.META['HTTP_X_FORWARDED_FOR'] = '0.0.0.0, 1.1.1.1, 7.7.7.7'
        assert self.view(self.request).status_code == 200

    def test_unique_clients_are_counted_independently_with_two_proxies(self):
        self.config_proxy(2)
        self.view(self.request)
        self.request.META['HTTP_X_FORWARDED_FOR'] = '0.0.0.0, 7.7.7.7, 2.2.2.2'
        assert self.view(self.request).status_code == 200


class SimpleRateThrottleTests(TestCase):

    def test_throttle_raises_error_if_scope_is_missing(self):
        with pytest.raises(ImproperlyConfigured):
            SimpleRateThrottle()

    def test_throttle_raises_error_if_rate_is_missing(self):
        SimpleRateThrottle.scope = 'test'
        with pytest.raises(ImproperlyConfigured):
            SimpleRateThrottle()

    def test_parse_rate_returns_tuple_with_none_if_rate_not_provided(self):
        SimpleRateThrottle.scope = 'anon'
        rate = SimpleRateThrottle().parse_rate(None)
        assert rate == (None, None)
