from django.test import TestCase
from rest_framework import serializers
from .models import BasicModel


class TestSerializerMetaClass(TestCase):
    def setUp(self):
        class FieldsSerializer(serializers.ModelSerializer):
            text = serializers.CharField()

            class Meta:
                model = BasicModel
                fields = ('text')

        class ExcludeSerializer(serializers.ModelSerializer):
            text = serializers.CharField()

            class Meta:
                model = BasicModel
                exclude = ('text')

        class FieldsAndExcludeSerializer(serializers.ModelSerializer):
            text = serializers.CharField()

            class Meta:
                model = BasicModel
                fields = ('text',)
                exclude = ('text',)

        self.fields_serializer = FieldsSerializer
        self.exclude_serializer = ExcludeSerializer
        self.faeSerializer = FieldsAndExcludeSerializer

    def test_meta_class_fields(self):
        object = BasicModel(text="Hello World.")
        serializer = self.fields_serializer(instance=object)

        with self.assertRaises(TypeError) as result:
            serializer.data

        exception = result.exception
        self.assertEqual(str(exception), "`fields` must be a list or tuple")

    def test_meta_class_exclude(self):
        object = BasicModel(text="Hello World.")
        serializer = self.exclude_serializer(instance=object)

        with self.assertRaises(TypeError) as result:
            serializer.data

        exception = result.exception
        self.assertEqual(str(exception), "`exclude` must be a list or tuple")

    def test_meta_class_fields_and_exclude(self):
        object = BasicModel(text="Hello World.")
        serializer = self.faeSerializer(instance=object)

        with self.assertRaises(AssertionError) as result:
            serializer.data

        exception = result.exception
        self.assertEqual(str(exception), "Cannot set both 'fields' and 'exclude'.")
