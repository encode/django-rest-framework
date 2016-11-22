import pytest

from rest_framework import serializers

from ..base import FieldValues


class TestCharField(FieldValues):
    """
    Valid and invalid values for `CharField`.
    """
    valid_inputs = {
        1: '1',
        'abc': 'abc'
    }
    invalid_inputs = {
        (): ['Not a valid string.'],
        True: ['Not a valid string.'],
        '': ['This field may not be blank.']
    }
    outputs = {
        1: '1',
        'abc': 'abc'
    }
    field = serializers.CharField()

    def test_trim_whitespace_default(self):
        field = serializers.CharField()
        assert field.to_internal_value(' abc ') == 'abc'

    def test_trim_whitespace_disabled(self):
        field = serializers.CharField(trim_whitespace=False)
        assert field.to_internal_value(' abc ') == ' abc '

    def test_disallow_blank_with_trim_whitespace(self):
        field = serializers.CharField(allow_blank=False, trim_whitespace=True)

        with pytest.raises(serializers.ValidationError) as exc_info:
            field.run_validation('   ')
        assert exc_info.value.detail == ['This field may not be blank.']
