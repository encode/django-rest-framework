import pytest

from rest_framework import serializers

from .base import FieldValues


class TestListField(FieldValues):
    """
    Values for `ListField` with IntegerField as child.
    """
    valid_inputs = [
        ([1, 2, 3], [1, 2, 3]),
        (['1', '2', '3'], [1, 2, 3]),
        ([], [])
    ]
    invalid_inputs = [
        ('not a list', ['Expected a list of items but got type "str".']),
        ([1, 2, 'error'], ['A valid integer is required.']),
        ({'one': 'two'}, ['Expected a list of items but got type "dict".'])
    ]
    outputs = [
        ([1, 2, 3], [1, 2, 3]),
        (['1', '2', '3'], [1, 2, 3])
    ]
    field = serializers.ListField(child=serializers.IntegerField())

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            serializers.ListField(child=serializers.IntegerField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )

    def test_collection_types_are_invalid_input(self):
        field = serializers.ListField(child=serializers.CharField())
        input_value = ({'one': 'two'})

        with pytest.raises(serializers.ValidationError) as exc_info:
            field.to_internal_value(input_value)
        assert exc_info.value.detail == ['Expected a list of items but got type "dict".']


class TestEmptyListField(FieldValues):
    """
    Values for `ListField` with allow_empty=False flag.
    """
    valid_inputs = {}
    invalid_inputs = [
        ([], ['This list may not be empty.'])
    ]
    outputs = {}
    field = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class TestUnvalidatedListField(FieldValues):
    """
    Values for `ListField` with no `child` argument.
    """
    valid_inputs = [
        ([1, '2', True, [4, 5, 6]], [1, '2', True, [4, 5, 6]]),
    ]
    invalid_inputs = [
        ('not a list', ['Expected a list of items but got type "str".']),
    ]
    outputs = [
        ([1, '2', True, [4, 5, 6]], [1, '2', True, [4, 5, 6]]),
    ]
    field = serializers.ListField()
