from django.http import QueryDict

import rest_framework
from rest_framework import serializers

from ..base import FieldValues


class TestMultipleChoiceField(FieldValues):
    """
    Valid and invalid values for `MultipleChoiceField`.
    """
    valid_inputs = {
        (): set(),
        ('aircon',): set(['aircon']),
        ('aircon', 'manual'): set(['aircon', 'manual']),
    }
    invalid_inputs = {
        'abc': ['Expected a list of items but got type "str".'],
        ('aircon', 'incorrect'): ['"incorrect" is not a valid choice.']
    }
    outputs = [
        (['aircon', 'manual', 'incorrect'], set(['aircon', 'manual', 'incorrect']))
    ]
    field = serializers.MultipleChoiceField(
        choices=[
            ('aircon', 'AirCon'),
            ('manual', 'Manual drive'),
            ('diesel', 'Diesel'),
        ]
    )

    def test_against_partial_and_full_updates(self):
        field = serializers.MultipleChoiceField(choices=(('a', 'a'), ('b', 'b')))
        field.partial = False
        assert field.get_value(QueryDict({})) == []
        field.partial = True
        assert field.get_value(QueryDict({})) == rest_framework.fields.empty


class TestEmptyMultipleChoiceField(FieldValues):
    """
    Invalid values for `MultipleChoiceField(allow_empty=False)`.
    """
    valid_inputs = {
    }
    invalid_inputs = (
        ([], ['This selection may not be empty.']),
    )
    outputs = [
    ]
    field = serializers.MultipleChoiceField(
        choices=[
            ('consistency', 'Consistency'),
            ('availability', 'Availability'),
            ('partition', 'Partition tolerance'),
        ],
        allow_empty=False
    )
