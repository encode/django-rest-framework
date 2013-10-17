"""
Tests to cover nested serializers.

Doesn't cover model serializers.
"""
from __future__ import unicode_literals
from django.test import TestCase
from rest_framework import serializers


class WritableNestedSerializerBasicTests(TestCase):
    """
    Tests for deserializing nested entities.
    Basic tests that use serializers that simply restore to dicts.
    """

    def setUp(self):
        class TrackSerializer(serializers.Serializer):
            order = serializers.IntegerField()
            title = serializers.CharField(max_length=100)
            duration = serializers.IntegerField()

        class AlbumSerializer(serializers.Serializer):
            album_name = serializers.CharField(max_length=100)
            artist = serializers.CharField(max_length=100)
            tracks = TrackSerializer(many=True)

        self.AlbumSerializer = AlbumSerializer

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

        serializer = self.AlbumSerializer(data=data)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, data)

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

        serializer = self.AlbumSerializer(data=data)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, expected_errors)

    def test_many_nested_validation_error(self):
        """
        Incorrect nested serialization should return appropriate error data
        when multiple entities are being deserialized.
        """

        data = [
            {
                'album_name': 'Russian Red',
                'artist': 'I Love Your Glasses',
                'tracks': [
                    {'order': 1, 'title': 'Cigarettes', 'duration': 121},
                    {'order': 2, 'title': 'No Past Land', 'duration': 198},
                    {'order': 3, 'title': 'They Don\'t Believe', 'duration': 191}
                ]
            },
            {
                'album_name': 'Discovery',
                'artist': 'Daft Punk',
                'tracks': [
                    {'order': 1, 'title': 'One More Time', 'duration': 235},
                    {'order': 2, 'title': 'Aerodynamic', 'duration': 184},
                    {'order': 3, 'title': 'Digital Love', 'duration': 'foobar'}
                ]
            }
        ]
        expected_errors = [
            {},
            {
                'tracks': [
                    {},
                    {},
                    {'duration': ['Enter a whole number.']}
                ]
            }
        ]

        serializer = self.AlbumSerializer(data=data, many=True)
        self.assertEqual(serializer.is_valid(), False)
        self.assertEqual(serializer.errors, expected_errors)


class WritableNestedSerializerObjectTests(TestCase):
    """
    Tests for deserializing nested entities.
    These tests use serializers that restore to concrete objects.
    """

    def setUp(self):
        # Couple of concrete objects that we're going to deserialize into
        class Track(object):
            def __init__(self, order, title, duration):
                self.order, self.title, self.duration = order, title, duration

            def __eq__(self, other):
                return (
                    self.order == other.order and
                    self.title == other.title and
                    self.duration == other.duration
                )

        class Album(object):
            def __init__(self, album_name, artist, tracks):
                self.album_name, self.artist, self.tracks = album_name, artist, tracks

            def __eq__(self, other):
                return (
                    self.album_name == other.album_name and
                    self.artist == other.artist and
                    self.tracks == other.tracks
                )

        # And their corresponding serializers
        class TrackSerializer(serializers.Serializer):
            order = serializers.IntegerField()
            title = serializers.CharField(max_length=100)
            duration = serializers.IntegerField()

            def restore_object(self, attrs, instance=None):
                return Track(attrs['order'], attrs['title'], attrs['duration'])

        class AlbumSerializer(serializers.Serializer):
            album_name = serializers.CharField(max_length=100)
            artist = serializers.CharField(max_length=100)
            tracks = TrackSerializer(many=True)

            def restore_object(self, attrs, instance=None):
                return Album(attrs['album_name'], attrs['artist'], attrs['tracks'])

        self.Album, self.Track = Album, Track
        self.AlbumSerializer = AlbumSerializer

    def test_nested_validation_success(self):
        """
        Correct nested serialization should return a restored object
        that corresponds to the input data.
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
        expected_object = self.Album(
            album_name='Discovery',
            artist='Daft Punk',
            tracks=[
                self.Track(order=1, title='One More Time', duration=235),
                self.Track(order=2, title='Aerodynamic', duration=184),
                self.Track(order=3, title='Digital Love', duration=239),
            ]
        )

        serializer = self.AlbumSerializer(data=data)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, expected_object)

    def test_many_nested_validation_success(self):
        """
        Correct nested serialization should return multiple restored objects
        that corresponds to the input data when multiple objects are
        being deserialized.
        """

        data = [
            {
                'album_name': 'Russian Red',
                'artist': 'I Love Your Glasses',
                'tracks': [
                    {'order': 1, 'title': 'Cigarettes', 'duration': 121},
                    {'order': 2, 'title': 'No Past Land', 'duration': 198},
                    {'order': 3, 'title': 'They Don\'t Believe', 'duration': 191}
                ]
            },
            {
                'album_name': 'Discovery',
                'artist': 'Daft Punk',
                'tracks': [
                    {'order': 1, 'title': 'One More Time', 'duration': 235},
                    {'order': 2, 'title': 'Aerodynamic', 'duration': 184},
                    {'order': 3, 'title': 'Digital Love', 'duration': 239}
                ]
            }
        ]
        expected_object = [
            self.Album(
                album_name='Russian Red',
                artist='I Love Your Glasses',
                tracks=[
                    self.Track(order=1, title='Cigarettes', duration=121),
                    self.Track(order=2, title='No Past Land', duration=198),
                    self.Track(order=3, title='They Don\'t Believe', duration=191),
                ]
            ),
            self.Album(
                album_name='Discovery',
                artist='Daft Punk',
                tracks=[
                    self.Track(order=1, title='One More Time', duration=235),
                    self.Track(order=2, title='Aerodynamic', duration=184),
                    self.Track(order=3, title='Digital Love', duration=239),
                ]
            )
        ]

        serializer = self.AlbumSerializer(data=data, many=True)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, expected_object)


class ForeignKeyNestedSerializerUpdateTests(TestCase):
    def setUp(self):
        class Artist(object):
            def __init__(self, name):
                self.name = name

            def __eq__(self, other):
                return self.name == other.name

        class Album(object):
            def __init__(self, name, artist):
                self.name, self.artist = name, artist

            def __eq__(self, other):
                return self.name == other.name and self.artist == other.artist

        class ArtistSerializer(serializers.Serializer):
            name = serializers.CharField()

            def restore_object(self, attrs, instance=None):
                if instance:
                    instance.name = attrs['name']
                else:
                    instance = Artist(attrs['name'])
                return instance

        class AlbumSerializer(serializers.Serializer):
            name = serializers.CharField()
            by = ArtistSerializer(source='artist')

            def restore_object(self, attrs, instance=None):
                if instance:
                    instance.name = attrs['name']
                    instance.artist = attrs['artist']
                else:
                    instance = Album(attrs['name'], attrs['artist'])
                return instance

        self.Artist = Artist
        self.Album = Album
        self.AlbumSerializer = AlbumSerializer

    def test_create_via_foreign_key_with_source(self):
        """
        Check that we can both *create* and *update* into objects across
        ForeignKeys that have a `source` specified.
        Regression test for #1170
        """
        data = {
            'name': 'Discovery',
            'by': {'name': 'Daft Punk'},
        }

        expected = self.Album(artist=self.Artist('Daft Punk'), name='Discovery')

        # create
        serializer = self.AlbumSerializer(data=data)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, expected)

        # update
        original = self.Album(artist=self.Artist('The Bats'), name='Free All the Monsters')
        serializer = self.AlbumSerializer(instance=original, data=data)
        self.assertEqual(serializer.is_valid(), True)
        self.assertEqual(serializer.object, expected)
