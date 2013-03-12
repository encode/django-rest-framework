from __future__ import unicode_literals
from django.test import TestCase
from rest_framework import serializers


class TrackSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    title = serializers.CharField(max_length=100)
    duration = serializers.IntegerField()


class AlbumSerializer(serializers.Serializer):
    album_name = serializers.CharField(max_length=100)
    artist = serializers.CharField(max_length=100)
    tracks = TrackSerializer(many=True)


class NestedSerializerTestCase(TestCase):
    def test_nested_validation_success(self):
        """
        Correct nested serialization should return the input data.
        """

        data = {
            'album_name': 'Discovery',
            'artist': 'Daft Punk',
            'tracks': [
                {'order': 1, 'title': 'One More Time', 'duration': 235},
                {'order': 2, 'title': 'Aerodynamic', 'duration': 184},
                {'order': 3, 'title': 'Digital Love', 'duration': 239}
            ]
        }

        serializer = AlbumSerializer(data=data)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.data, data)

    def test_nested_validation_error(self):
        """
        Incorrect nested serialization should return appropriate error data.
        """

        data = {
            'album_name': 'Discovery',
            'artist': 'Daft Punk',
            'tracks': [
                {'order': 1, 'title': 'One More Time', 'duration': 235},
                {'order': 2, 'title': 'Aerodynamic', 'duration': 184},
                {'order': 3, 'title': 'Digital Love', 'duration': 'foobar'}
            ]
        }
        expected_errors = {
            'tracks': [
                {},
                {},
                {'duration': ['Enter a whole number.']}
            ]
        }

        serializer = AlbumSerializer(data=data)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, expected_errors)
