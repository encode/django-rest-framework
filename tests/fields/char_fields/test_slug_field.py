from rest_framework import serializers

from ..base import FieldValues


class TestSlugField(FieldValues):
    """
    Valid and invalid values for `SlugField`.
    """
    valid_inputs = {
        'slug-99': 'slug-99',
    }
    invalid_inputs = {
        'slug 99': ['Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.']
    }
    outputs = {}
    field = serializers.SlugField()
