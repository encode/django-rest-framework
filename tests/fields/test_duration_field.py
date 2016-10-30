import datetime

from rest_framework import serializers

from .base import FieldValues


class TestDurationField(FieldValues):
    """
    Valid and invalid values for `DurationField`.
    """
    valid_inputs = {
        '13': datetime.timedelta(seconds=13),
        '3 08:32:01.000123': datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123),
        '08:01': datetime.timedelta(minutes=8, seconds=1),
        datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123): datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123),
        3600: datetime.timedelta(hours=1),
    }
    invalid_inputs = {
        'abc': ['Duration has wrong format. Use one of these formats instead: [DD] [HH:[MM:]]ss[.uuuuuu].'],
        '3 08:32 01.123': ['Duration has wrong format. Use one of these formats instead: [DD] [HH:[MM:]]ss[.uuuuuu].'],
    }
    outputs = {
        datetime.timedelta(days=3, hours=8, minutes=32, seconds=1, microseconds=123): '3 08:32:01.000123',
    }
    field = serializers.DurationField()
