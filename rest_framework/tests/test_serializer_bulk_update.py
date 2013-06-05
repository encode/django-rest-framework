"""
Tests to cover bulk create and update using serializers.
"""
from __future__ import unicode_literals
from django.test import TestCase
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
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, data)

    def test_bulk_create_errors(self):
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
                'id': 'foo',
                'title': 'The wind-up bird chronicle',
                'author': 'Haruki Murakami'
            }
        ]
        expected_errors = [
            {},
            {},
            {'id': ['Enter a whole number.']}
        ]

        serializer = self.BookSerializer(data=data, many=True)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, expected_errors)

    def test_invalid_list_datatype(self):
        """
        Data containing list of incorrect data type should return errors.
        """
        data = ['foo', 'bar', 'baz']
        serializer = self.BookSerializer(data=data, many=True)
        self.assertEqual(serializer.is_valid(), False)

        expected_errors = [
                {'non_field_errors': ['Invalid data']},
                {'non_field_errors': ['Invalid data']},
                {'non_field_errors': ['Invalid data']}
        ]

        self.assertEqual(serializer.errors, expected_errors)

    def test_invalid_single_datatype(self):
        """
        Data containing a single incorrect data type should return errors.
        """
        data = 123
        serializer = self.BookSerializer(data=data, many=True)
        self.assertEqual(serializer.is_valid(), False)

        expected_errors = {'non_field_errors': ['Expected a list of items.']}

        self.assertEqual(serializer.errors, expected_errors)

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
        self.assertEqual(serializer.is_valid(), False)

        expected_errors = {'non_field_errors': ['Expected a list of items.']}

        self.assertEqual(serializer.errors, expected_errors)


class BulkUpdateSerializerTests(TestCase):
    """
    Updating multiple instances using serializers.
    """

    def setUp(self):
        class Book(object):
            """
            A data type that can be persisted to a mock storage backend
            with `.save()` and `.delete()`.
            """
            object_map = {}

            def __init__(self, id, title, author):
                self.id = id
                self.title = title
                self.author = author

            def save(self):
                Book.object_map[self.id] = self

            def delete(self):
                del Book.object_map[self.id]

        class BookSerializer(serializers.Serializer):
            id = serializers.IntegerField()
            title = serializers.CharField(max_length=100)
            author = serializers.CharField(max_length=100)

            def restore_object(self, attrs, instance=None):
                if instance:
                    instance.id = attrs['id']
                    instance.title = attrs['title']
                    instance.author = attrs['author']
                    return instance
                return Book(**attrs)

        self.Book = Book
        self.BookSerializer = BookSerializer

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

        for item in data:
            book = Book(item['id'], item['title'], item['author'])
            book.save()

    def books(self):
        """
        Return all the objects in the mock storage backend.
        """
        return self.Book.object_map.values()

    def test_bulk_update_success(self):
        """
        Correct bulk update serialization should return the input data.
        """
        data = [
            {
                'id': 0,
                'title': 'The electric kool-aid acid test',
                'author': 'Tom Wolfe'
            }, {
                'id': 2,
                'title': 'Kafka on the shore',
                'author': 'Haruki Murakami'
            }
        ]
        serializer = self.BookSerializer(self.books(), data=data, many=True, allow_add_remove=True)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.data, data)
        serializer.save()
        new_data = self.BookSerializer(self.books(), many=True).data

        self.assertEqual(data, new_data)

    def test_bulk_update_and_create(self):
        """
        Bulk update serialization may also include created items.
        """
        data = [
            {
                'id': 0,
                'title': 'The electric kool-aid acid test',
                'author': 'Tom Wolfe'
            }, {
                'id': 3,
                'title': 'Kafka on the shore',
                'author': 'Haruki Murakami'
            }
        ]
        serializer = self.BookSerializer(self.books(), data=data, many=True, allow_add_remove=True)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.data, data)
        serializer.save()
        new_data = self.BookSerializer(self.books(), many=True).data
        self.assertEqual(data, new_data)

    def test_bulk_update_invalid_create(self):
        """
        Bulk update serialization without allow_add_remove may not create items.
        """
        data = [
            {
                'id': 0,
                'title': 'The electric kool-aid acid test',
                'author': 'Tom Wolfe'
            }, {
                'id': 3,
                'title': 'Kafka on the shore',
                'author': 'Haruki Murakami'
            }
        ]
        expected_errors = [
            {},
            {'non_field_errors': ['Cannot create a new item, only existing items may be updated.']}
        ]
        serializer = self.BookSerializer(self.books(), data=data, many=True)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, expected_errors)

    def test_bulk_update_error(self):
        """
        Incorrect bulk update serialization should return error data.
        """
        data = [
            {
                'id': 0,
                'title': 'The electric kool-aid acid test',
                'author': 'Tom Wolfe'
            }, {
                'id': 'foo',
                'title': 'Kafka on the shore',
                'author': 'Haruki Murakami'
            }
        ]
        expected_errors = [
            {},
            {'id': ['Enter a whole number.']}
        ]
        serializer = self.BookSerializer(self.books(), data=data, many=True, allow_add_remove=True)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, expected_errors)
