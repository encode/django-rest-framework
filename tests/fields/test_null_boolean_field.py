from rest_framework import serializers

from .base import FieldValues


class TestNullBooleanField(FieldValues):
    """
    Valid and invalid values for `BooleanField`.
    """
    valid_inputs = {
        'true': True,
        'false': False,
        'null': None,
        True: True,
        False: False,
        None: None
    }
    invalid_inputs = {
        'foo': ['"foo" is not a valid boolean.'],
    }
    outputs = {
        'true': True,
        'false': False,
        'null': None,
        True: True,
        False: False,
        None: None,
        'other': True
    }
    field = serializers.NullBooleanField()
