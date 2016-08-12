# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from django import forms
from django.core.files.uploadhandler import (
    MemoryFileUploadHandler, TemporaryFileUploadHandler
)
from django.test import TestCase
from django.utils.six.moves import StringIO

from rest_framework.exceptions import ParseError
from rest_framework.parsers import FileUploadParser, FormParser


class Form(forms.Form):
    field1 = forms.CharField(max_length=3)
    field2 = forms.CharField()


class TestFormParser(TestCase):
    def setUp(self):
        self.string = "field1=abc&field2=defghijk"

    def test_parse(self):
        """ Make sure the `QueryDict` works OK """
        parser = FormParser()

        stream = StringIO(self.string)
        data = parser.parse(stream)

        self.assertEqual(Form(data).is_valid(), True)


class TestFileUploadParser(TestCase):
    def setUp(self):
        class MockRequest(object):
            pass
        from io import BytesIO
        self.stream = BytesIO(
            "Test text file".encode('utf-8')
        )
        request = MockRequest()
        request.upload_handlers = (MemoryFileUploadHandler(),)
        request.META = {
            'HTTP_CONTENT_DISPOSITION': 'Content-Disposition: inline; filename=file.txt',
            'HTTP_CONTENT_LENGTH': 14,
        }
        self.parser_context = {'request': request, 'kwargs': {}}

    def test_parse(self):
        """
        Parse raw file upload.
        """
        parser = FileUploadParser()
        self.stream.seek(0)
        data_and_files = parser.parse(self.stream, None, self.parser_context)
        file_obj = data_and_files.files['file']
        self.assertEqual(file_obj._size, 14)

    def test_parse_missing_filename(self):
        """
        Parse raw file upload when filename is missing.
        """
        parser = FileUploadParser()
        self.stream.seek(0)
        self.parser_context['request'].META['HTTP_CONTENT_DISPOSITION'] = ''
        with pytest.raises(ParseError) as excinfo:
            parser.parse(self.stream, None, self.parser_context)
        assert str(excinfo.value) == 'Missing filename. Request should include a Content-Disposition header with a filename parameter.'

    def test_parse_missing_filename_multiple_upload_handlers(self):
        """
        Parse raw file upload with multiple handlers when filename is missing.
        Regression test for #2109.
        """
        parser = FileUploadParser()
        self.stream.seek(0)
        self.parser_context['request'].upload_handlers = (
            MemoryFileUploadHandler(),
            MemoryFileUploadHandler()
        )
        self.parser_context['request'].META['HTTP_CONTENT_DISPOSITION'] = ''
        with pytest.raises(ParseError) as excinfo:
            parser.parse(self.stream, None, self.parser_context)
        assert str(excinfo.value) == 'Missing filename. Request should include a Content-Disposition header with a filename parameter.'

    def test_parse_missing_filename_large_file(self):
        """
        Parse raw file upload when filename is missing with TemporaryFileUploadHandler.
        """
        parser = FileUploadParser()
        self.stream.seek(0)
        self.parser_context['request'].upload_handlers = (
            TemporaryFileUploadHandler(),
        )
        self.parser_context['request'].META['HTTP_CONTENT_DISPOSITION'] = ''
        with pytest.raises(ParseError) as excinfo:
            parser.parse(self.stream, None, self.parser_context)
        assert str(excinfo.value) == 'Missing filename. Request should include a Content-Disposition header with a filename parameter.'

    def test_get_filename(self):
        parser = FileUploadParser()
        filename = parser.get_filename(self.stream, None, self.parser_context)
        self.assertEqual(filename, 'file.txt')

    def test_get_encoded_filename(self):
        parser = FileUploadParser()

        self.__replace_content_disposition('inline; filename*=utf-8\'\'ÀĥƦ.txt')
        filename = parser.get_filename(self.stream, None, self.parser_context)
        self.assertEqual(filename, 'ÀĥƦ.txt')

        self.__replace_content_disposition('inline; filename=fallback.txt; filename*=utf-8\'\'ÀĥƦ.txt')
        filename = parser.get_filename(self.stream, None, self.parser_context)
        self.assertEqual(filename, 'ÀĥƦ.txt')

        self.__replace_content_disposition('inline; filename=fallback.txt; filename*=utf-8\'en-us\'ÀĥƦ.txt')
        filename = parser.get_filename(self.stream, None, self.parser_context)
        self.assertEqual(filename, 'ÀĥƦ.txt')

    def __replace_content_disposition(self, disposition):
        self.parser_context['request'].META['HTTP_CONTENT_DISPOSITION'] = disposition
