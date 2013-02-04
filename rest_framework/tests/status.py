"""Tests for the status module"""
from django.test import TestCase
from rest_framework import status


class TestStatus(TestCase):
    """Simple sanity tests to check the status module"""

    def test_status_HTTP_100_CONTINUE(self):
        """Ensure that HTTP_100_CONTINUE equals 100."""
        self.assertEquals(status.HTTP_100_CONTINUE, 100)

    def test_status_HTTP_101_SWITCHING_PROTOCOLS(self):
        """Ensure that HTTP_101_SWITCHING_PROTOCOLS equals 101."""
        self.assertEquals(status.HTTP_101_SWITCHING_PROTOCOLS, 101)

    def test_status_HTTP_200_OK(self):
        """Ensure that HTTP_200_OK equals 200."""
        self.assertEquals(status.HTTP_200_OK, 200)

    def test_status_HTTP_201_CREATED(self):
        """Ensure that HTTP_201_CREATED equals 201."""
        self.assertEquals(status.HTTP_201_CREATED, 201)

    def test_status_HTTP_202_ACCEPTED(self):
        """Ensure that HTTP_202_ACCEPTED equals 202."""
        self.assertEquals(status.HTTP_202_ACCEPTED, 202)

    def test_status_HTTP_203_NON_AUTHORITATIVE_INFORMATION(self):
        """Ensure that HTTP_203_NON_AUTHORITATIVE_INFORMATION equals 203."""
        self.assertEquals(status.HTTP_203_NON_AUTHORITATIVE_INFORMATION, 203)

    def test_status_HTTP_204_NO_CONTENT(self):
        """Ensure that HTTP_204_NO_CONTENT equals 204."""
        self.assertEquals(status.HTTP_204_NO_CONTENT, 204)

    def test_status_HTTP_205_RESET_CONTENT(self):
        """Ensure that HTTP_205_RESET_CONTENT equals 205."""
        self.assertEquals(status.HTTP_205_RESET_CONTENT, 205)

    def test_status_HTTP_206_PARTIAL_CONTENT(self):
        """Ensure that HTTP_206_PARTIAL_CONTENT equals 206."""
        self.assertEquals(status.HTTP_206_PARTIAL_CONTENT, 206)

    def test_status_HTTP_300_MULTIPLE_CHOICES(self):
        """Ensure that HTTP_300_MULTIPLE_CHOICES equals 300."""
        self.assertEquals(status.HTTP_300_MULTIPLE_CHOICES, 300)

    def test_status_HTTP_301_MOVED_PERMANENTLY(self):
        """Ensure that HTTP_301_MOVED_PERMANENTLY equals 301."""
        self.assertEquals(status.HTTP_301_MOVED_PERMANENTLY, 301)

    def test_status_HTTP_302_FOUND(self):
        """Ensure that HTTP_302_FOUND equals 302."""
        self.assertEquals(status.HTTP_302_FOUND, 302)

    def test_status_HTTP_303_SEE_OTHER(self):
        """Ensure that HTTP_303_SEE_OTHER equals 303."""
        self.assertEquals(status.HTTP_303_SEE_OTHER, 303)

    def test_status_HTTP_304_NOT_MODIFIED(self):
        """Ensure that HTTP_304_NOT_MODIFIED equals 304."""
        self.assertEquals(status.HTTP_304_NOT_MODIFIED, 304)

    def test_status_HTTP_305_USE_PROXY(self):
        """Ensure that HTTP_305_USE_PROXY equals 305."""
        self.assertEquals(status.HTTP_305_USE_PROXY, 305)

    def test_status_HTTP_306_RESERVED(self):
        """Ensure that HTTP_306_RESERVED equals 306."""
        self.assertEquals(status.HTTP_306_RESERVED, 306)

    def test_status_HTTP_307_TEMPORARY_REDIRECT(self):
        """Ensure that HTTP_307_TEMPORARY_REDIRECT equals 307."""
        self.assertEquals(status.HTTP_307_TEMPORARY_REDIRECT, 307)

    def test_status_HTTP_400_BAD_REQUEST(self):
        """Ensure that HTTP_400_BAD_REQUEST equals 400."""
        self.assertEquals(status.HTTP_400_BAD_REQUEST, 400)

    def test_status_HTTP_401_UNAUTHORIZED(self):
        """Ensure that HTTP_401_UNAUTHORIZED equals 401."""
        self.assertEquals(status.HTTP_401_UNAUTHORIZED, 401)

    def test_status_HTTP_402_PAYMENT_REQUIRED(self):
        """Ensure that HTTP_402_PAYMENT_REQUIRED equals 402."""
        self.assertEquals(status.HTTP_402_PAYMENT_REQUIRED, 402)

    def test_status_HTTP_403_FORBIDDEN(self):
        """Ensure that HTTP_403_FORBIDDEN equals 403."""
        self.assertEquals(status.HTTP_403_FORBIDDEN, 403)

    def test_status_HTTP_404_NOT_FOUND(self):
        """Ensure that HTTP_404_NOT_FOUND equals 404."""
        self.assertEquals(status.HTTP_404_NOT_FOUND, 404)

    def test_status_HTTP_405_METHOD_NOT_ALLOWED(self):
        """Ensure that HTTP_405_METHOD_NOT_ALLOWED equals 405."""
        self.assertEquals(status.HTTP_405_METHOD_NOT_ALLOWED, 405)

    def test_status_HTTP_406_NOT_ACCEPTABLE(self):
        """Ensure that HTTP_406_NOT_ACCEPTABLE equals 406."""
        self.assertEquals(status.HTTP_406_NOT_ACCEPTABLE, 406)

    def test_status_HTTP_407_PROXY_AUTHENTICATION_REQUIRED(self):
        """Ensure that HTTP_407_PROXY_AUTHENTICATION_REQUIRED equals 407."""
        self.assertEquals(status.HTTP_407_PROXY_AUTHENTICATION_REQUIRED, 407)

    def test_status_HTTP_408_REQUEST_TIMEOUT(self):
        """Ensure that HTTP_408_REQUEST_TIMEOUT equals 408."""
        self.assertEquals(status.HTTP_408_REQUEST_TIMEOUT, 408)

    def test_status_HTTP_409_CONFLICT(self):
        """Ensure that HTTP_409_CONFLICT equals 409."""
        self.assertEquals(status.HTTP_409_CONFLICT, 409)

    def test_status_HTTP_410_GONE(self):
        """Ensure that HTTP_410_GONE equals 410."""
        self.assertEquals(status.HTTP_410_GONE, 410)

    def test_status_HTTP_411_LENGTH_REQUIRED(self):
        """Ensure that HTTP_411_LENGTH_REQUIRED equals 411."""
        self.assertEquals(status.HTTP_411_LENGTH_REQUIRED, 411)

    def test_status_HTTP_412_PRECONDITION_FAILED(self):
        """Ensure that HTTP_412_PRECONDITION_FAILED equals 412."""
        self.assertEquals(status.HTTP_412_PRECONDITION_FAILED, 412)

    def test_status_HTTP_413_REQUEST_ENTITY_TOO_LARGE(self):
        """Ensure that HTTP_413_REQUEST_ENTITY_TOO_LARGE equals 413."""
        self.assertEquals(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, 413)

    def test_status_HTTP_414_REQUEST_URI_TOO_LONG(self):
        """Ensure that HTTP_414_REQUEST_URI_TOO_LONG equals 414."""
        self.assertEquals(status.HTTP_414_REQUEST_URI_TOO_LONG, 414)

    def test_status_HTTP_415_UNSUPPORTED_MEDIA_TYPE(self):
        """Ensure that HTTP_415_UNSUPPORTED_MEDIA_TYPE equals 415."""
        self.assertEquals(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, 415)

    def test_status_HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE(self):
        """Ensure that HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE equals 416."""
        self.assertEquals(status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE, 416)

    def test_status_HTTP_417_EXPECTATION_FAILED(self):
        """Ensure that HTTP_417_EXPECTATION_FAILED equals 417."""
        self.assertEquals(status.HTTP_417_EXPECTATION_FAILED, 417)

    def test_status_HTTP_428_PRECONDITION_REQUIRED(self):
        """Ensure that HTTP_428_PRECONDITION_REQUIRED equals 428."""
        self.assertEquals(status.HTTP_428_PRECONDITION_REQUIRED, 428)

    def test_status_HTTP_429_TOO_MANY_REQUESTS(self):
        """Ensure that HTTP_429_TOO_MANY_REQUESTS equals 428."""
        self.assertEquals(status.HTTP_429_TOO_MANY_REQUESTS, 429)

    def test_status_HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE(self):
        """Ensure that HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE equals 431."""
        self.assertEquals(status.HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE, 431)

    def test_status_HTTP_500_INTERNAL_SERVER_ERROR(self):
        """Ensure that HTTP_500_INTERNAL_SERVER_ERROR equals 500."""
        self.assertEquals(status.HTTP_500_INTERNAL_SERVER_ERROR, 500)

    def HTTP_501_NOT_IMPLEMENTED(self):
        """Ensure that HTTP_501_NOT_IMPLEMENTED equals 501."""
        self.assertEquals(status.HTTP_501_NOT_IMPLEMENTED, 501)

    def test_status_HTTP_502_BAD_GATEWAY(self):
        """Ensure that HTTP_502_BAD_GATEWAY equals 502."""
        self.assertEquals(status.HTTP_502_BAD_GATEWAY, 502)

    def test_status_HTTP_503_SERVICE_UNAVAILABLE(self):
        """Ensure that HTTP_503_SERVICE_UNAVAILABLE equals 503."""
        self.assertEquals(status.HTTP_503_SERVICE_UNAVAILABLE, 503)

    def test_status_HTTP_504_GATEWAY_TIMEOUT(self):
        """Ensure that HTTP_504_GATEWAY_TIMEOUT equals 504."""
        self.assertEquals(status.HTTP_504_GATEWAY_TIMEOUT, 504)

    def test_status_HTTP_505_HTTP_VERSION_NOT_SUPPORTED(self):
        """Ensure that HTTP_505_HTTP_VERSION_NOT_SUPPORTED equals 505."""
        self.assertEquals(status.HTTP_505_HTTP_VERSION_NOT_SUPPORTED, 505)

    def test_status_HTTP_511_NETWORK_AUTHENTICATION_REQUIRED(self):
        """Ensure that HTTP_511_NETWORK_AUTHENTICATION_REQUIRED equals 511."""
        self.assertEquals(status.HTTP_511_NETWORK_AUTHENTICATION_REQUIRED, 511)
