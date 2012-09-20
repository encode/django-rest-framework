import datetime
from django.test import TestCase
from rest_framework import serializers


class Comment(object):
    def __init__(self, email, content, created):
        self.email = email
        self.content = content
        self.created = created or datetime.datetime.now()

    def __eq__(self, other):
        return all([getattr(self, attr) == getattr(other, attr)
                    for attr in ('email', 'content', 'created')])


class CommentSerializer(serializers.Serializer):
    email = serializers.EmailField()
    content = serializers.CharField(max_length=1000)
    created = serializers.DateTimeField()

    def restore_object(self, data, instance=None):
        if instance is None:
            return Comment(**data)
        for key, val in data.items():
            setattr(instance, key, val)
        return instance


class BasicTests(TestCase):
    def setUp(self):
        self.comment = Comment(
            'tom@example.com',
            'Happy new year!',
            datetime.datetime(2012, 1, 1)
        )
        self.data = {
            'email': 'tom@example.com',
            'content': 'Happy new year!',
            'created': datetime.datetime(2012, 1, 1)
        }

    def test_empty(self):
        serializer = CommentSerializer()
        expected = {
            'email': '',
            'content': '',
            'created': None
        }
        self.assertEquals(serializer.data, expected)

    def test_serialization(self):
        serializer = CommentSerializer(instance=self.comment)
        expected = self.data
        self.assertEquals(serializer.data, expected)

    def test_deserialization_for_create(self):
        serializer = CommentSerializer(self.data)
        expected = self.comment
        self.assertEquals(serializer.is_valid(), True)
        self.assertEquals(serializer.object, expected)
        self.assertFalse(serializer.object is expected)

    def test_deserialization_for_update(self):
        serializer = CommentSerializer(self.data, instance=self.comment)
        expected = self.comment
        self.assertEquals(serializer.is_valid(), True)
        self.assertEquals(serializer.object, expected)
        self.assertTrue(serializer.object is expected)


class ValidationTests(TestCase):
    def setUp(self):
        self.comment = Comment(
            'tom@example.com',
            'Happy new year!',
            datetime.datetime(2012, 1, 1)
        )
        self.data = {
            'email': 'tom@example.com',
            'content': 'x' * 1001,
            'created': datetime.datetime(2012, 1, 1)
        }

    def test_deserialization_for_create(self):
        serializer = CommentSerializer(self.data)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'content': [u'Ensure this value has at most 1000 characters (it has 1001).']})

    def test_deserialization_for_update(self):
        serializer = CommentSerializer(self.data, instance=self.comment)
        self.assertEquals(serializer.is_valid(), False)
        self.assertEquals(serializer.errors, {'content': [u'Ensure this value has at most 1000 characters (it has 1001).']})


class MetadataTests(TestCase):
    # def setUp(self):
    #     self.comment = Comment(
    #         'tomchristie',
    #         'Happy new year!',
    #         datetime.datetime(2012, 1, 1)
    #     )
    #     self.data = {
    #         'email': 'tomchristie',
    #         'content': 'Happy new year!',
    #         'created': datetime.datetime(2012, 1, 1)
    #     }

    def test_empty(self):
        serializer = CommentSerializer()
        expected = {
            'email': serializers.CharField,
            'content': serializers.CharField,
            'created': serializers.DateTimeField
        }
        for field_name, field in expected.items():
            self.assertTrue(isinstance(serializer.data.fields[field_name], field))
