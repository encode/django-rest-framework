from __future__ import unicode_literals
from django.test import TestCase
from rest_framework import serializers
from rest_framework.compat import BytesIO
from rest_framework.compat import six
import datetime


class UploadedFile(object):
    def __init__(self, file, created=None):
        self.file = file
        self.created = created or datetime.datetime.now()


class UploadedFileSerializer(serializers.Serializer):
    file = serializers.FileField()
    created = serializers.DateTimeField()

    def restore_object(self, attrs, instance=None):
        if instance:
            instance.file = attrs['file']
            instance.created = attrs['created']
            return instance
        return UploadedFile(**attrs)


class FileSerializerTests(TestCase):
    def test_create(self):
        now = datetime.datetime.now()
        file = BytesIO(six.b('stuff'))
        file.name = 'stuff.txt'
        file.size = len(file.getvalue())
        serializer = UploadedFileSerializer(data={'created': now}, files={'file': file})
        uploaded_file = UploadedFile(file=file, created=now)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.object.created, uploaded_file.created)
        self.assertEqual(serializer.object.file, uploaded_file.file)
        self.assertFalse(serializer.object is uploaded_file)

    def test_creation_failure(self):
        """
        Passing files=None should result in an ValidationError

        Regression test for:
        https://github.com/tomchristie/django-rest-framework/issues/542
        """
        now = datetime.datetime.now()

        serializer = UploadedFileSerializer(data={'created': now})
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)
