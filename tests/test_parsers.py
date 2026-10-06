import io
import math
from urllib.parse import quote

import pytest
from django import forms
from django.conf import settings
from django.core.files.uploadhandler import (
    MemoryFileUploadHandler, TemporaryFileUploadHandler
)
from django.http.request import RawPostDataException
from django.test import TestCase

from rest_framework.exceptions import ParseError
from rest_framework.parsers import (
    FileUploadParser, FormParser, JSONParser, MultiPartParser, get_encoding
)
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory


class Form(forms.Form):
    field1 = forms.CharField(max_length=3)
    field2 = forms.CharField()


class TestFormParser(TestCase):
    def setUp(self):
        self.string = "field1=abc&field2=defghijk"

    def test_parse(self):
        """ Make sure the `QueryDict` works OK """
        parser = FormParser()

        stream = io.StringIO(self.string)
        data = parser.parse(stream)

        assert Form(data).is_valid() is True


class TestFileUploadParser(TestCase):
    def setUp(self):
        class MockRequest:
            pass
        self.stream = io.BytesIO(b"Test text file")
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
        assert file_obj.size == 14

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
        assert filename == 'file.txt'

    def test_get_encoded_filename(self):
        parser = FileUploadParser()
        # RFC 8187 requires non-ASCII to be percent-encoded
        encoded = quote('ÀĥƦ.txt')

        self.__replace_content_disposition(f"inline; filename*=utf-8''{encoded}")
        filename = parser.get_filename(self.stream, None, self.parser_context)
        assert filename == 'ÀĥƦ.txt'

        self.__replace_content_disposition(f"inline; filename=fallback.txt; filename*=utf-8''{encoded}")
        filename = parser.get_filename(self.stream, None, self.parser_context)
        assert filename == 'ÀĥƦ.txt'

        self.__replace_content_disposition(f"inline; filename=fallback.txt; filename*=utf-8'en-us'{encoded}")
        filename = parser.get_filename(self.stream, None, self.parser_context)
        assert filename == 'ÀĥƦ.txt'

    def __replace_content_disposition(self, disposition):
        self.parser_context['request'].META['HTTP_CONTENT_DISPOSITION'] = disposition


class TestJSONParser(TestCase):
    def bytes(self, value):
        return io.BytesIO(value.encode())

    def test_float_strictness(self):
        parser = JSONParser()

        # Default to strict
        for value in ['Infinity', '-Infinity', 'NaN']:
            with pytest.raises(ParseError):
                parser.parse(self.bytes(value))

        parser.strict = False
        assert parser.parse(self.bytes('Infinity')) == float('inf')
        assert parser.parse(self.bytes('-Infinity')) == float('-inf')
        assert math.isnan(parser.parse(self.bytes('NaN')))


class TestGetEncoding(TestCase):
    def test_defaults_to_default_charset(self):
        assert get_encoding({}) == settings.DEFAULT_CHARSET

    def test_accepts_text_encodings(self):
        for encoding in ['utf-8', 'UTF8', 'ascii', 'latin-1', 'utf-16', 'utf-32']:
            with self.subTest(encoding=encoding):
                assert get_encoding({'encoding': encoding}) == encoding

    def test_rejects_non_text_encodings(self):
        # Short aliases, as a `charset=` parameter would carry them.
        # `undefined` is a text codec in name only: it fails on every input.
        for encoding in ['bz2', 'zlib', 'base64', 'hex', 'rot13', 'undefined',
                         'not-a-real-encoding']:
            with self.subTest(encoding=encoding):
                with pytest.raises(ParseError):
                    get_encoding({'encoding': encoding})


class TestRequestCharset(TestCase):
    unsupported_message = 'Unsupported charset "%s" in request Content-Type header.'

    # Codecs that transform bytes rather than decode text. `zip` is an alias
    # of `zlib_codec`, so this also checks the codec is resolved rather than
    # the name matched.
    byte_transforms = (
        'base64_codec', 'bz2_codec', 'hex_codec', 'quopri_codec', 'rot_13',
        'uu_codec', 'zlib_codec', 'zip',
    )

    def test_json_parser_honours_a_text_charset(self):
        # utf-16 is not the default and its bytes are not valid utf-8, so this
        # only passes if the charset the client named was the one used.
        stream = io.BytesIO('{"field1": "ÀĥƦ"}'.encode('utf-16'))
        data = JSONParser().parse(stream, parser_context={'encoding': 'utf-16'})

        assert data == {'field1': 'ÀĥƦ'}

    def test_form_parser_honours_a_text_charset(self):
        stream = io.BytesIO('field1=À&field2=x'.encode('iso-8859-1'))
        data = FormParser().parse(stream, parser_context={'encoding': 'iso-8859-1'})

        assert data['field1'] == 'À'

    def test_json_parser_rejects_a_byte_transform_charset(self):
        for charset in self.byte_transforms:
            with self.subTest(charset=charset):
                with pytest.raises(ParseError) as excinfo:
                    JSONParser().parse(
                        io.BytesIO(b'{}'), parser_context={'encoding': charset}
                    )
                assert str(excinfo.value) == self.unsupported_message % charset

    def test_form_parser_rejects_a_byte_transform_charset(self):
        for charset in self.byte_transforms:
            with self.subTest(charset=charset):
                with pytest.raises(ParseError) as excinfo:
                    FormParser().parse(
                        io.BytesIO(b'field1=x'), parser_context={'encoding': charset}
                    )
                assert str(excinfo.value) == self.unsupported_message % charset

    def test_multipart_parser_rejects_a_byte_transform_charset(self):
        request = APIRequestFactory().post('/', {'field1': 'x'})
        for charset in self.byte_transforms:
            with self.subTest(charset=charset):
                with pytest.raises(ParseError) as excinfo:
                    MultiPartParser().parse(
                        io.BytesIO(request.body),
                        request.content_type,
                        parser_context={'request': request, 'encoding': charset}
                    )
                assert str(excinfo.value) == self.unsupported_message % charset

    def test_unresolvable_charset_is_rejected(self):
        # Django drops charsets `codecs.lookup()` cannot resolve, so this only
        # happens with a hand-built `parser_context`. Still not a server error.
        with pytest.raises(ParseError) as excinfo:
            JSONParser().parse(
                io.BytesIO(b'{}'), parser_context={'encoding': 'no-such-charset'}
            )

        assert str(excinfo.value) == self.unsupported_message % 'no-such-charset'


class TestPOSTAccessed(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_post_accessed_in_post_method(self):
        django_request = self.factory.post('/', {'foo': 'bar'})
        request = Request(django_request, parsers=[FormParser(), MultiPartParser()])
        django_request.POST
        assert request.POST == {'foo': ['bar']}
        assert request.data == {'foo': ['bar']}

    def test_post_accessed_in_post_method_with_json_parser(self):
        django_request = self.factory.post('/', {'foo': 'bar'})
        request = Request(django_request, parsers=[JSONParser()])
        django_request.POST
        assert request.POST == {}
        assert request.data == {}

    def test_post_accessed_in_put_method(self):
        django_request = self.factory.put('/', {'foo': 'bar'})
        request = Request(django_request, parsers=[FormParser(), MultiPartParser()])
        django_request.POST
        assert request.POST == {'foo': ['bar']}
        assert request.data == {'foo': ['bar']}

    def test_request_read_before_parsing(self):
        django_request = self.factory.put('/', {'foo': 'bar'})
        request = Request(django_request, parsers=[FormParser(), MultiPartParser()])
        django_request.read()
        with pytest.raises(RawPostDataException):
            request.POST
        with pytest.raises(RawPostDataException):
            request.POST
            request.data
