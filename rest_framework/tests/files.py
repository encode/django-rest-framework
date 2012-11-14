import StringIO
import datetime

from django.test import TestCase

from rest_framework import serializers


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
        file = StringIO.StringIO('stuff')
        file.name = 'stuff.txt'
        file.size = file.len
        serializer = UploadedFileSerializer(data={'created': now}, files={'file': file})
        uploaded_file = UploadedFile(file=file, created=now)
        self.assertTrue(serializer.is_valid())
        self.assertEquals(serializer.object.created, uploaded_file.created)
        self.assertEquals(serializer.object.file, uploaded_file.file)
        self.assertFalse(serializer.object is uploaded_file)
