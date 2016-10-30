import os

from rest_framework import serializers

from ..base import FieldValues


class TestFilePathField(FieldValues):
    """
    Valid and invalid values for `FilePathField`
    """

    valid_inputs = {
        __file__: __file__,
    }
    invalid_inputs = {
        'wrong_path': ['"wrong_path" is not a valid path choice.']
    }
    outputs = {
    }
    field = serializers.FilePathField(
        path=os.path.abspath(os.path.dirname(__file__))
    )
