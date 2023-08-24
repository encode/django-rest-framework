import ipaddress
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from django.test import TestCase

from rest_framework.compat import coreapi
from rest_framework.utils.encoders import JSONEncoder
from rest_framework.utils.serializer_helpers import ReturnList

utc = timezone.utc


class MockList:
    def tolist(self):
        return [1, 2, 3]


class JSONEncoderTests(TestCase):
    """
    Tests the JSONEncoder method
    """

    def setUp(self):
        self.encoder = JSONEncoder()

    def test_encode_decimal(self):
        """
        Tests encoding a decimal
        """
        d = Decimal(3.14)
        assert self.encoder.default(d) == float(d)

    def test_encode_datetime(self):
        """
        Tests encoding a datetime object
        """
        current_time = datetime.now()
        assert self.encoder.default(current_time) == current_time.isoformat()
        current_time_utc = current_time.replace(tzinfo=utc)
        assert self.encoder.default(current_time_utc) == current_time.isoformat() + 'Z'

    def test_encode_time(self):
        """
        Tests encoding a timezone
        """
        current_time = datetime.now().time()
        assert self.encoder.default(current_time) == current_time.isoformat()

    def test_encode_time_tz(self):
        """
        Tests encoding a timezone aware timestamp
        """
        current_time = datetime.now().time()
        current_time = current_time.replace(tzinfo=utc)
        with pytest.raises(ValueError):
            self.encoder.default(current_time)

    def test_encode_date(self):
        """
        Tests encoding a date object
        """
        current_date = date.today()
        assert self.encoder.default(current_date) == current_date.isoformat()

    def test_encode_timedelta(self):
        """
        Tests encoding a timedelta object
        """
        delta = timedelta(hours=1)
        assert self.encoder.default(delta) == str(delta.total_seconds())

    def test_encode_uuid(self):
        """
        Tests encoding a UUID object
        """
        unique_id = uuid4()
        assert self.encoder.default(unique_id) == str(unique_id)

    def test_encode_ipaddress_ipv4address(self):
        """
        Tests encoding ipaddress IPv4Address object
        """
        obj = ipaddress.IPv4Address("192.168.1.1")
        assert self.encoder.default(obj) == str(obj)

    def test_encode_ipaddress_ipv6address(self):
        """
        Tests encoding ipaddress IPv6Address object
        """
        obj = ipaddress.IPv6Address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        assert self.encoder.default(obj) == str(obj)

    def test_encode_ipaddress_ipv4network(self):
        """
        Tests encoding ipaddress IPv4Network object
        """
        obj = ipaddress.IPv4Network("192.0.2.8/29")
        assert self.encoder.default(obj) == str(obj)

    def test_encode_ipaddress_ipv6network(self):
        """
        Tests encoding ipaddress IPv4Network object
        """
        obj = ipaddress.IPv6Network("2001:4860:0000::0000/32")
        assert self.encoder.default(obj) == str(obj)

    def test_encode_ipaddress_ipv4interface(self):
        """
        Tests encoding ipaddress IPv4Interface object
        """
        obj = ipaddress.IPv4Interface("192.0.2.8/29")
        assert self.encoder.default(obj) == str(obj)

    def test_encode_ipaddress_ipv6interface(self):
        """
        Tests encoding ipaddress IPv4Network object
        """
        obj = ipaddress.IPv6Interface("2001:4860:4860::8888/32")
        assert self.encoder.default(obj) == str(obj)

    @pytest.mark.skipif(not coreapi, reason='coreapi is not installed')
    def test_encode_coreapi_raises_error(self):
        """
        Tests encoding a coreapi objects raises proper error
        """
        with pytest.raises(RuntimeError):
            self.encoder.default(coreapi.Document())

        with pytest.raises(RuntimeError):
            self.encoder.default(coreapi.Error())

    def test_encode_object_with_tolist(self):
        """
        Tests encoding a object with tolist method
        """
        foo = MockList()
        assert self.encoder.default(foo) == [1, 2, 3]

    def test_encode_empty_returnlist(self):
        """
        Tests encoding an empty ReturnList
        """
        foo = ReturnList(serializer=None)
        assert self.encoder.default(foo) == []
