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

class DataFlatener(object):
    """Utility object for flatening dictionaries of lists. Useful for "urlencoded" decoded data."""

    def flatten_data(self, data):
        """Given a data dictionary {<key>: <value_list>}, returns a flattened dictionary
        with information provided by the method "is_a_list"."""
        flatdata = dict()
        for key, attr_value in data.items():
            if self.is_a_list(key):
                if isinstance(attr_value, list):
                    flatdata[key] = attr_value
                else:
                    flatdata[key] = [attr_value]
            else:
                if isinstance(attr_value, list):
                    flatdata[key] = attr_value[0]
                else:
                    flatdata[key] = attr_value 
        return flatdata

    def is_a_list(self, key, val):
        """Returns True if the parameter with name *key* is expected to be a list, or False otherwise.
        *val* which is the received value for parameter *key* can be used to guess the answer."""
        return False

class FormParser(BaseParser, DataFlatener):
    """The default parser for form data.
    Return a dict containing a single value for each non-reserved parameter.

    In order to handle select multiple (and having possibly more than a single value for each parameter),
    you can customize the output by subclassing the method 'is_a_list'.

    """
    # TODO: writing tests for PUT files + normal data
    media_type = 'application/x-www-form-urlencoded'

    """The value of the parameter when the select multiple is empty.
    Browsers are usually stripping the select multiple that have no option selected from the parameters sent.
    A common hack to avoid this is to send the parameter with a value specifying that the list is empty.
    This value will always be stripped before the data is returned."""
    EMPTY_VALUE = '_empty'

    def parse(self, input):
        data = parse_qs(input)

        # Flatening data and removing EMPTY_VALUEs from the lists
        data = self.flatten_data(data)
        for key in filter(lambda k: self.is_a_list(k), data):
            self.remove_empty_val(data[key])

        # Strip any parameters that we are treating as reserved
        for key in data.keys():
            if key in self.resource.RESERVED_FORM_PARAMS:
                data.pop(key)
        return data

    def remove_empty_val(self, val_list):
        """ """
        while(1): # Because there might be several times EMPTY_VALUE in the list
            try: 
                ind = val_list.index(self.EMPTY_VALUE)
            except ValueError:
                break
            else:
                val_list.pop(ind) 

# TODO: Allow parsers to specify multiple media_types
class MultipartParser(BaseParser, DataFlatener):
    media_type = 'multipart/form-data'

    def parse(self, input):

        request = self.resource.request
        #TODO : that's pretty dumb : files are loaded with
        #upload_handlers, but as we read the request body completely (input),
        #then it kind of misses the point. Why not input as a stream ?
        upload_handlers = request._get_upload_handlers()
        django_mpp = DjangoMPParser(request.META, StringIO(input), upload_handlers)
        data, files = django_mpp.parse()

        # Flatening data, files and combining them
        data = self.flatten_data(data)
        files = self.flatten_data(files)
        data.update(files)
        
        # Strip any parameters that we are treating as reserved
        for key in data.keys():
            if key in self.resource.RESERVED_FORM_PARAMS:
                data.pop(key)
        return data
