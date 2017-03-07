"""
Tests to cover bulk create and update using serializers.
"""
from __future__ import unicode_literals

from django.test import TestCase
from django.utils import six

from rest_framework import serializers


class BulkCreateSerializerTests(TestCase):
    """
    Creating multiple instances using serializers.
    """

    def setUp(self):
        class BookSerializer(serializers.Serializer):
            id = serializers.IntegerField()
            title = serializers.CharField(max_length=100)
            author = serializers.CharField(max_length=100)

        self.BookSerializer = BookSerializer

    def test_bulk_create_success(self):
        """
        Correct bulk update serialization should return the input data.
        """

        data = [
            {
                'id': 0,
                'title': 'The electric kool-aid acid test',
                'author': 'Tom Wolfe'
            }, {
                'id': 1,
                'title': 'If this is a man',
                'author': 'Primo Levi'
            }, {
                'id': 2,
                'title': 'The wind-up bird chronicle',
                'author': 'Haruki Murakami'
            }
        ]

        serializer = self.BookSerializer(data=data, many=True)
        assert serializer.is_valid() is True
        assert serializer.validated_data == data
        assert serializer.errors == []

    def test_bulk_create_errors(self):
        """
        Incorrect bulk create serialization should return errors.
        """

        data = [
            {
                'id': 0,
                'title': 'The electric kool-aid acid test',
                'author': 'Tom Wolfe'
            }, {
                'id': 1,
                'title': 'If this is a man',
                'author': 'Primo Levi'
            }, {
                'id': 'foo',
                'title': 'The wind-up bird chronicle',
                'author': 'Haruki Murakami'
            }
        ]
        expected_errors = [
            {},
            {},
            {'id': ['A valid integer is required.']}
        ]

        serializer = self.BookSerializer(data=data, many=True)
        assert serializer.is_valid() is False
        assert serializer.errors == expected_errors
        assert serializer.validated_data == []

    def test_invalid_list_datatype(self):
        """
        Data containing list of incorrect data type should return errors.
        """
        data = ['foo', 'bar', 'baz']
        serializer = self.BookSerializer(data=data, many=True)
        assert serializer.is_valid() is False

        text_type_string = six.text_type.__name__
        message = 'Invalid data. Expected a dictionary, but got %s.' % text_type_string
        expected_errors = [
            {'non_field_errors': [message]},
            {'non_field_errors': [message]},
            {'non_field_errors': [message]}
        ]

        assert serializer.errors == expected_errors

    def test_invalid_single_datatype(self):
        """
        Data containing a single incorrect data type should return errors.
        """
        data = 123
        serializer = self.BookSerializer(data=data, many=True)
        assert serializer.is_valid() is False

        expected_errors = {'non_field_errors': ['Expected a list of items but got type "int".']}

        assert serializer.errors == expected_errors

    def test_invalid_single_object(self):
        """
        Data containing only a single object, instead of a list of objects
        should return errors.
        """
        data = {
            'id': 0,
            'title': 'The electric kool-aid acid test',
            'author': 'Tom Wolfe'
        }
        serializer = self.BookSerializer(data=data, many=True)
        assert serializer.is_valid() is False

        expected_errors = {'non_field_errors': ['Expected a list of items but got type "dict".']}

        assert serializer.errors == expected_errors
