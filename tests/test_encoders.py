from datetime import date, datetime, timedelta, tzinfo
from decimal import Decimal
from uuid import uuid4

from django.test import TestCase

from rest_framework.utils.encoders import JSONEncoder


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
        assert d == float(d)

    def test_encode_datetime(self):
        """
        Tests encoding a datetime object
        """
        current_time = datetime.now()
        assert self.encoder.default(current_time) == current_time.isoformat()

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

        class UTC(tzinfo):
            """
            Class extending tzinfo to mimic UTC time
            """
            def utcoffset(self, dt):
                return timedelta(0)

            def tzname(self, dt):
                return "UTC"

            def dst(self, dt):
                return timedelta(0)

        current_time = datetime.now().time()
        current_time = current_time.replace(tzinfo=UTC())
        with self.assertRaises(ValueError):
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
