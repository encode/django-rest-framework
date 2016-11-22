from rest_framework import serializers

from ..base import FieldValues


class TestEmailField(FieldValues):
    """
    Valid and invalid values for `EmailField`.
    """
    valid_inputs = {
        'example@example.com': 'example@example.com',
        ' example@example.com ': 'example@example.com',
    }
    invalid_inputs = {
        'examplecom': ['Enter a valid email address.']
    }
    outputs = {}
    field = serializers.EmailField()
