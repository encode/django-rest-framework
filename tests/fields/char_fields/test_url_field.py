from rest_framework import serializers

from ..base import FieldValues


class TestURLField(FieldValues):
    """
    Valid and invalid values for `URLField`.
    """
    valid_inputs = {
        'http://example.com': 'http://example.com',
    }
    invalid_inputs = {
        'example.com': ['Enter a valid URL.']
    }
    outputs = {}
    field = serializers.URLField()
