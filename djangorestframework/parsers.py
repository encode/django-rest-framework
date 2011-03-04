from StringIO import StringIO

from django.http.multipartparser import MultiPartParser as DjangoMPParser

from djangorestframework.response import ResponseException
from djangorestframework import status

try:
    import json
except ImportError:
    import simplejson as json

try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

class ParserMixin(object):
    parsers = ()

    def parse(self, content_type, content):
        # See RFC 2616 sec 3 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec3.html#sec3.7
        split = content_type.split(';', 1)
        if len(split) > 1:
            content_type = split[0]
        content_type = content_type.strip()

        media_type_to_parser = dict([(parser.media_type, parser) for parser in self.parsers])

        try:
            parser = media_type_to_parser[content_type]
        except KeyError:
            raise ResponseException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                                    {'error': 'Unsupported media type in request \'%s\'.' % content_type})
        
        return parser(self).parse(content)

    @property
    def parsed_media_types(self):
        """Return an list of all the media types that this ParserMixin can parse."""
        return [parser.media_type for parser in self.parsers]
    
    @property
    def default_parser(self):
        """Return the ParerMixin's most prefered emitter.
        (This has no behavioural effect, but is may be used by documenting emitters)"""        
        return self.parsers[0]


class BaseParser(object):
    """All parsers should extend BaseParser, specifing a media_type attribute,
    and overriding the parse() method."""

    media_type = None

    def __init__(self, resource):
        """Initialise the parser with the Resource instance as state,
        in case the parser needs to access any metadata on the Resource object."""
        self.resource = resource
    
    def parse(self, input):
        """Given some serialized input, return the deserialized output.
        The input will be the raw request content body.  The return value may be of
        any type, but for many parsers/inputs it might typically be a dict."""
        return input


class JSONParser(BaseParser):
    media_type = 'application/json'

    def parse(self, input):
        try:
            return json.loads(input)
        except ValueError, exc:
            raise ResponseException(status.HTTP_400_BAD_REQUEST, {'detail': 'JSON parse error - %s' % str(exc)})


class XMLParser(BaseParser):
    media_type = 'application/xml'


class FormParser(BaseParser):
    """The default parser for form data.
    Return a dict containing a single value for each non-reserved parameter.
    """
    # TODO: not good, because posted/put lists are flattened !!!
    media_type = 'application/x-www-form-urlencoded'

    def parse(self, input):
        request = self.resource.request

        if request.method == 'PUT':
            data = parse_qs(input)
            # Flattening the parsed query data
            for key, val in data.items():
                data[key] = val[0]

        if request.method == 'POST':
            # Django has already done the form parsing for us.
            data = dict(request.POST.items())

        # Strip any parameters that we are treating as reserved
        for key in data:
            if key in self.resource.RESERVED_FORM_PARAMS:
                data.pop(key)
        return data

# TODO: Allow parsers to specify multiple media_types
class MultipartParser(FormParser):
    media_type = 'multipart/form-data'

    def parse(self, input):
        request = self.resource.request

        if request.method == 'PUT':
            upload_handlers = request._get_upload_handlers()
            django_mpp = DjangoMPParser(request.META, StringIO(input), upload_handlers)
            data, files = django_mpp.parse()
            data = dict(data)
            files = dict(files)

        if request.method == 'POST':
            # Django has already done the form parsing for us.
            data = dict(request.POST)
            files = dict(request.FILES)

        # Flattening, then merging the POSTED/PUT data/files
        for key, val in dict(data).items():
            data[key] = val[0]
        for key, val in dict(files).items():
            files[key] = val[0].read()
        data.update(files)
        
        # Strip any parameters that we are treating as reserved
        for key in data:
            if key in self.resource.RESERVED_FORM_PARAMS:
                data.pop(key)
        return data

