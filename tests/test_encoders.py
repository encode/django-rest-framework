# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.test import TestCase
from django.utils import six
from django.utils.timezone import utc

from rest_framework.compat import coreapi
from rest_framework.utils.encoders import JSONEncoder


class MockList(object):
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
        assert self.encoder.default(current_time) == current_time.isoformat()[:12]

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

    def test_encode_float(self):
        """
        Tests encoding floats with special values
        """

        f = [3.141592653, float('inf'), float('-inf'), float('nan')]
        assert self.encoder.encode(f) == '[3.141592653, "Infinity", "-Infinity", "NaN"]'

        encoder = JSONEncoder(allow_nan=False)
        try:
            encoder.encode(f)
        except ValueError:
            pass
        else:
            assert False

    def test_encode_string(self):
        """
        Tests encoding string
        """

        if six.PY2:
            encoder2 = JSONEncoder(encoding='latin_1', check_circular=False)
            assert encoder2.encode(['foo☺']) == '["foo\\u00e2\\u0098\\u00ba"]'
