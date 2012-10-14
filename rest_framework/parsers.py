"""
Django supports parsing the content of an HTTP request, but only for form POST requests.
That behavior is sufficient for dealing with standard HTML forms, but it doesn't map well
to general HTTP requests.

We need a method to be able to:

1.) Determine the parsed content on a request for methods other than POST (eg typically also PUT)

2.) Determine the parsed content on a request for media types other than application/x-www-form-urlencoded
   and multipart/form-data.  (eg also handle multipart/json)
"""

from django.http import QueryDict
from django.http.multipartparser import MultiPartParser as DjangoMultiPartParser
from django.http.multipartparser import MultiPartParserError
from django.utils import simplejson as json
from rest_framework.compat import yaml, ETParseError
from rest_framework.exceptions import ParseError
from xml.etree import ElementTree as ET
from xml.parsers.expat import ExpatError
import datetime
import decimal
from io import BytesIO


class DataAndFiles(object):
    def __init__(self, data, files):
        self.data = data
        self.files = files


class BaseParser(object):
    """
    All parsers should extend `BaseParser`, specifying a `media_type`
    attribute, and overriding the `.parse_stream()` method.
    """

    media_type = None

    def parse(self, string_or_stream, **opts):
        """
        The main entry point to parsers.  This is a light wrapper around
        `parse_stream`, that instead handles both string and stream objects.
        """
        if isinstance(string_or_stream, basestring):
            stream = BytesIO(string_or_stream)
        else:
            stream = string_or_stream
        return self.parse_stream(stream, **opts)

    def parse_stream(self, stream, **opts):
        """
        Given a stream to read from, return the deserialized output.
        Should return parsed data, or a DataAndFiles object consisting of the
        parsed data and files.
        """
        raise NotImplementedError(".parse_stream() must be overridden.")


class JSONParser(BaseParser):
    """
    Parses JSON-serialized data.
    """

    media_type = 'application/json'

    def parse_stream(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will be an object which is the parsed content of the response.
        `files` will always be `None`.
        """
        try:
            return json.load(stream)
        except ValueError, exc:
            raise ParseError('JSON parse error - %s' % unicode(exc))


class YAMLParser(BaseParser):
    """
    Parses YAML-serialized data.
    """

    media_type = 'application/yaml'

    def parse_stream(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will be an object which is the parsed content of the response.
        `files` will always be `None`.
        """
        try:
            return yaml.safe_load(stream)
        except (ValueError, yaml.parser.ParserError), exc:
            raise ParseError('YAML parse error - %s' % unicode(exc))


class FormParser(BaseParser):
    """
    Parser for form data.
    """

    media_type = 'application/x-www-form-urlencoded'

    def parse_stream(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will be a :class:`QueryDict` containing all the form parameters.
        `files` will always be :const:`None`.
        """
        data = QueryDict(stream.read())
        return data


class MultiPartParser(BaseParser):
    """
    Parser for multipart form data, which may include file data.
    """

    media_type = 'multipart/form-data'

    def parse_stream(self, stream, **opts):
        """
        Returns a DataAndFiles object.

        `.data` will be a `QueryDict` containing all the form parameters.
        `.files` will be a `QueryDict` containing all the form files.
        """
        meta = opts['meta']
        upload_handlers = opts['upload_handlers']
        try:
            parser = DjangoMultiPartParser(meta, stream, upload_handlers)
            data, files = parser.parse()
            return DataAndFiles(data, files)
        except MultiPartParserError, exc:
            raise ParseError('Multipart form parse error - %s' % unicode(exc))


class XMLParser(BaseParser):
    """
    XML parser.
    """

    media_type = 'application/xml'

    def parse_stream(self, stream, **opts):
        try:
            tree = ET.parse(stream)
        except (ExpatError, ETParseError, ValueError), exc:
            raise ParseError('XML parse error - %s' % unicode(exc))
        data = self._xml_convert(tree.getroot())

        return data

    def _xml_convert(self, element):
        """
        convert the xml `element` into the corresponding python object
        """

        children = element.getchildren()

        if len(children) == 0:
            return self._type_convert(element.text)
        else:
            # if the fist child tag is list-item means all children are list-item
            if children[0].tag == "list-item":
                data = []
                for child in children:
                    data.append(self._xml_convert(child))
            else:
                data = {}
                for child in children:
                    data[child.tag] = self._xml_convert(child)

            return data

    def _type_convert(self, value):
        """
        Converts the value returned by the XMl parse into the equivalent
        Python type
        """
        if value is None:
            return value

        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            pass

        try:
            return int(value)
        except ValueError:
            pass

        try:
            return decimal.Decimal(value)
        except decimal.InvalidOperation:
            pass

        return value
