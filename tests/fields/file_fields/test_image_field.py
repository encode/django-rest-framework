from rest_framework import serializers

from ..base import FieldValues
from .helpers import MockFile


# Stub out mock Django `forms.ImageField` class so we don't *actually*
# call into it's regular validation, or require PIL for testing.
class FailImageValidation(object):
    def to_python(self, value):
        raise serializers.ValidationError(self.error_messages['invalid_image'])


class PassImageValidation(object):
    def to_python(self, value):
        return value


class TestInvalidImageField(FieldValues):
    """
    Values for an invalid `ImageField`.
    """
    valid_inputs = {}
    invalid_inputs = [
        (MockFile(name='example.txt', size=10), [
            'Upload a valid image. The file you uploaded was either not an image or a corrupted image.'])
    ]
    outputs = {}
    field = serializers.ImageField(_DjangoImageField=FailImageValidation)


class TestValidImageField(FieldValues):
    """
    Values for an valid `ImageField`.
    """
    valid_inputs = [
        (MockFile(name='example.txt', size=10), MockFile(name='example.txt', size=10))
    ]
    invalid_inputs = {}
    outputs = {}
    field = serializers.ImageField(_DjangoImageField=PassImageValidation)
