import re

from rest_framework import serializers

from ..base import FieldValues


class TestRegexField(FieldValues):
    """
    Valid and invalid values for `RegexField`.
    """
    valid_inputs = {
        'a9': 'a9',
    }
    invalid_inputs = {
        'A9': ["This value does not match the required pattern."]
    }
    outputs = {}
    field = serializers.RegexField(regex='[a-z][0-9]')


class TestiCompiledRegexField(FieldValues):
    """
    Valid and invalid values for `RegexField`.
    """
    valid_inputs = {
        'a9': 'a9',
    }
    invalid_inputs = {
        'A9': ["This value does not match the required pattern."]
    }
    outputs = {}
    field = serializers.RegexField(regex=re.compile('[a-z][0-9]'))
