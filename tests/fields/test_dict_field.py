import pytest

from rest_framework import serializers

from .base import FieldValues


class TestDictField(FieldValues):
    """
    Values for `ListField` with CharField as child.
    """
    valid_inputs = [
        ({'a': 1, 'b': '2', 3: 3}, {'a': '1', 'b': '2', '3': '3'}),
    ]
    invalid_inputs = [
        ({'a': 1, 'b': None}, ['This field may not be null.']),
        ('not a dict', ['Expected a dictionary of items but got type "str".']),
    ]
    outputs = [
        ({'a': 1, 'b': '2', 3: 3}, {'a': '1', 'b': '2', '3': '3'}),
    ]
    field = serializers.DictField(child=serializers.CharField())

    def test_no_source_on_child(self):
        with pytest.raises(AssertionError) as exc_info:
            serializers.DictField(child=serializers.CharField(source='other'))

        assert str(exc_info.value) == (
            "The `source` argument is not meaningful when applied to a `child=` field. "
            "Remove `source=` from the field declaration."
        )

    def test_allow_null(self):
        """
        If `allow_null=True` then `None` is a valid input.
        """
        field = serializers.DictField(allow_null=True)
        output = field.run_validation(None)
        assert output is None


class TestDictFieldWithNullChild(FieldValues):
    """
    Values for `ListField` with allow_null CharField as child.
    """
    valid_inputs = [
        ({'a': None, 'b': '2', 3: 3}, {'a': None, 'b': '2', '3': '3'}),
    ]
    invalid_inputs = [
    ]
    outputs = [
        ({'a': None, 'b': '2', 3: 3}, {'a': None, 'b': '2', '3': '3'}),
    ]
    field = serializers.DictField(child=serializers.CharField(allow_null=True))


class TestUnvalidatedDictField(FieldValues):
    """
    Values for `ListField` with no `child` argument.
    """
    valid_inputs = [
        ({'a': 1, 'b': [4, 5, 6], 1: 123}, {'a': 1, 'b': [4, 5, 6], '1': 123}),
    ]
    invalid_inputs = [
        ('not a dict', ['Expected a dictionary of items but got type "str".']),
    ]
    outputs = [
        ({'a': 1, 'b': [4, 5, 6]}, {'a': 1, 'b': [4, 5, 6]}),
    ]
    field = serializers.DictField()
