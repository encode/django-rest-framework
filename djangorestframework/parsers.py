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
from djangorestframework.compat import yaml
from djangorestframework.exceptions import ParseError
from djangorestframework.utils.mediatypes import media_type_matches
from xml.etree import ElementTree as ET
from djangorestframework.compat import ETParseError
from xml.parsers.expat import ExpatError
import datetime
import decimal


__all__ = (
    'BaseParser',
    'JSONParser',
    'PlainTextParser',
    'FormParser',
    'MultiPartParser',
    'YAMLParser',
    'XMLParser'
)


class BaseParser(object):
    """
    All parsers should extend :class:`BaseParser`, specifying a :attr:`media_type` attribute,
    and overriding the :meth:`parse` method.
    """

    media_type = None

    def can_handle_request(self, content_type):
        """
        Returns :const:`True` if this parser is able to deal with the given *content_type*.

        The default implementation for this function is to check the *content_type*
        argument against the :attr:`media_type` attribute set on the class to see if
        they match.

        This may be overridden to provide for other behavior, but typically you'll
        instead want to just set the :attr:`media_type` attribute on the class.
        """
        return media_type_matches(self.media_type, content_type)

    def parse(self, stream, **opts):
        """
        Given a *stream* to read from, return the deserialized output.
        Should return a 2-tuple of (data, files).
        """
        raise NotImplementedError(".parse() Must be overridden to be implemented.")


class JSONParser(BaseParser):
    """
    Parses JSON-serialized data.
    """

    media_type = 'application/json'

    def parse(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will be an object which is the parsed content of the response.
        `files` will always be `None`.
        """
        try:
            return (json.load(stream), None)
        except ValueError, exc:
            raise ParseError('JSON parse error - %s' % unicode(exc))


class YAMLParser(BaseParser):
    """
    Parses YAML-serialized data.
    """

    media_type = 'application/yaml'

    def parse(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will be an object which is the parsed content of the response.
        `files` will always be `None`.
        """
        try:
            return (yaml.safe_load(stream), None)
        except (ValueError, yaml.parser.ParserError), exc:
            raise ParseError('YAML parse error - %s' % unicode(exc))


class PlainTextParser(BaseParser):
    """
    Plain text parser.
    """

    media_type = 'text/plain'

    def parse(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will simply be a string representing the body of the request.
        `files` will always be `None`.
        """
        return (stream.read(), None)


class FormParser(BaseParser):
    """
    Parser for form data.
    """

    media_type = 'application/x-www-form-urlencoded'

    def parse(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will be a :class:`QueryDict` containing all the form parameters.
        `files` will always be :const:`None`.
        """
        data = QueryDict(stream.read())
        return (data, None)


class MultiPartParser(BaseParser):
    """
    Parser for multipart form data, which may include file data.
    """

    media_type = 'multipart/form-data'

    def parse(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will be a :class:`QueryDict` containing all the form parameters.
        `files` will be a :class:`QueryDict` containing all the form files.
        """
        meta = opts['meta']
        upload_handlers = opts['upload_handlers']
        try:
            parser = DjangoMultiPartParser(meta, stream, upload_handlers)
            return parser.parse()
        except MultiPartParserError, exc:
            raise ParseError('Multipart form parse error - %s' % unicode(exc))


class XMLParser(BaseParser):
    """
    XML parser.
    """

    media_type = 'application/xml'

    def parse(self, stream, **opts):
        """
        Returns a 2-tuple of `(data, files)`.

        `data` will simply be a string representing the body of the request.
        `files` will always be `None`.
        """
        try:
            tree = ET.parse(stream)
        except (ExpatError, ETParseError, ValueError), exc:
            raise ParseError('XML parse error - %s' % unicode(exc))
        data = self._xml_convert(tree.getroot())

        return (data, None)

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


DEFAULT_PARSERS = (
    JSONParser,
    FormParser,
    MultiPartParser,
    XMLParser
)

if yaml:
    DEFAULT_PARSERS += (YAMLParser, )
else:
    YAMLParser = None
