import pytest

from rest_framework import serializers

from .base import FieldValues


class TestBooleanField(FieldValues):
    """
    Valid and invalid values for `BooleanField`.
    """
    valid_inputs = {
        'true': True,
        'false': False,
        '1': True,
        '0': False,
        1: True,
        0: False,
        True: True,
        False: False,
    }
    invalid_inputs = {
        'foo': ['"foo" is not a valid boolean.'],
        None: ['This field may not be null.']
    }
    outputs = {
        'true': True,
        'false': False,
        '1': True,
        '0': False,
        1: True,
        0: False,
        True: True,
        False: False,
        'other': True
    }
    field = serializers.BooleanField()

    def test_disallow_unhashable_collection_types(self):
        inputs = (
            [],
            {},
        )
        field = serializers.BooleanField()
        for input_value in inputs:
            with pytest.raises(serializers.ValidationError) as exc_info:
                field.run_validation(input_value)
            expected = ['"{0}" is not a valid boolean.'.format(input_value)]
            assert exc_info.value.detail == expected
