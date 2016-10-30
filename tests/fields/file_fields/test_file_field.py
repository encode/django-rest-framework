from rest_framework import serializers

from ..base import FieldValues
from .helpers import MockFile


class MockRequest:
    def build_absolute_uri(self, value):
        return 'http://example.com' + value


class TestFileField(FieldValues):
    """
    Values for `FileField`.
    """
    valid_inputs = [
        (MockFile(name='example', size=10), MockFile(name='example', size=10))
    ]
    invalid_inputs = [
        ('invalid', ['The submitted data was not a file. Check the encoding type on the form.']),
        (MockFile(name='example.txt', size=0), ['The submitted file is empty.']),
        (MockFile(name='', size=10), ['No filename could be determined.']),
        (MockFile(name='x' * 100, size=10),
         ['Ensure this filename has at most 10 characters (it has 100).'])
    ]
    outputs = [
        (MockFile(name='example.txt', url='/example.txt'), '/example.txt'),
        ('', None)
    ]
    field = serializers.FileField(max_length=10)


class TestFieldFieldWithName(FieldValues):
    """
    Values for `FileField` with a filename output instead of URLs.
    """
    valid_inputs = {}
    invalid_inputs = {}
    outputs = [
        (MockFile(name='example.txt', url='/example.txt'), 'example.txt')
    ]
    field = serializers.FileField(use_url=False)


class TestFileFieldContext:
    def test_fully_qualified_when_request_in_context(self):
        field = serializers.FileField(max_length=10)
        field._context = {'request': MockRequest()}
        obj = MockFile(name='example.txt', url='/example.txt')
        value = field.to_representation(obj)
        assert value == 'http://example.com/example.txt'
