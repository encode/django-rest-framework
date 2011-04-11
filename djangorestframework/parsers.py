"""Django supports parsing the content of an HTTP request, but only for form POST requests.
That behaviour is sufficient for dealing with standard HTML forms, but it doesn't map well
to general HTTP requests.

We need a method to be able to:

1) Determine the parsed content on a request for methods other than POST (eg typically also PUT)
2) Determine the parsed content on a request for media types other than application/x-www-form-urlencoded
   and multipart/form-data.  (eg also handle multipart/json)
"""
from django.http.multipartparser import MultiPartParser as DjangoMPParser
from djangorestframework.response import ErrorResponse
from djangorestframework import status
from djangorestframework.utils import as_tuple
from djangorestframework.mediatypes import MediaType

try:
    import json
except ImportError:
    import simplejson as json

try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs



class BaseParser(object):
    """All parsers should extend BaseParser, specifying a media_type attribute,
    and overriding the parse() method."""
    media_type = None

    def __init__(self, view):
        """
        Initialise the parser with the View instance as state,
        in case the parser needs to access any metadata on the View object.
        
        """
        self.view = view
    
    @classmethod
    def handles(self, media_type):
        """
        Returns `True` if this parser is able to deal with the given MediaType.
        """
        return media_type.match(self.media_type)

    def parse(self, stream):
        """Given a stream to read from, return the deserialized output.
        The return value may be of any type, but for many parsers it might typically be a dict-like object."""
        raise NotImplementedError("BaseParser.parse() Must be overridden to be implemented.")


class JSONParser(BaseParser):
    media_type = MediaType('application/json')

    def parse(self, stream):
        try:
            return json.load(stream)
        except ValueError, exc:
            raise ErrorResponse(status.HTTP_400_BAD_REQUEST, {'detail': 'JSON parse error - %s' % str(exc)})


class DataFlatener(object):
    """Utility object for flatening dictionaries of lists. Useful for "urlencoded" decoded data."""

    def flatten_data(self, data):
        """Given a data dictionary {<key>: <value_list>}, returns a flattened dictionary
        with information provided by the method "is_a_list"."""
        flatdata = dict()
        for key, val_list in data.items():
            if self.is_a_list(key, val_list):
                flatdata[key] = val_list
            else:
                if val_list:
                    flatdata[key] = val_list[0]
                else:
                    # If the list is empty, but the parameter is not a list,
                    # we strip this parameter.
                    data.pop(key)
        return flatdata

    def is_a_list(self, key, val_list):
        """Returns True if the parameter with name *key* is expected to be a list, or False otherwise.
        *val_list* which is the received value for parameter *key* can be used to guess the answer."""
        return False


class PlainTextParser(BaseParser):
    """
    Plain text parser.
    
    Simply returns the content of the stream
    """
    media_type = MediaType('text/plain')

    def parse(self, stream):
        return stream.read()


class FormParser(BaseParser, DataFlatener):
    """The default parser for form data.
    Return a dict containing a single value for each non-reserved parameter.

    In order to handle select multiple (and having possibly more than a single value for each parameter),
    you can customize the output by subclassing the method 'is_a_list'."""

    media_type = MediaType('application/x-www-form-urlencoded')

    """The value of the parameter when the select multiple is empty.
    Browsers are usually stripping the select multiple that have no option selected from the parameters sent.
    A common hack to avoid this is to send the parameter with a value specifying that the list is empty.
    This value will always be stripped before the data is returned."""
    EMPTY_VALUE = '_empty'
    RESERVED_FORM_PARAMS = ('csrfmiddlewaretoken',)

    def parse(self, stream):
        data = parse_qs(stream.read(), keep_blank_values=True)

        # removing EMPTY_VALUEs from the lists and flatening the data 
        for key, val_list in data.items():
            self.remove_empty_val(val_list)
        data = self.flatten_data(data)

        # Strip any parameters that we are treating as reserved
        for key in data.keys():
            if key in self.RESERVED_FORM_PARAMS:
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


class MultipartData(dict):
    def __init__(self, data, files):
        dict.__init__(self, data)
        self.FILES = files

class MultipartParser(BaseParser, DataFlatener):
    media_type = MediaType('multipart/form-data')
    RESERVED_FORM_PARAMS = ('csrfmiddlewaretoken',)

    def parse(self, stream):
        upload_handlers = self.view.request._get_upload_handlers()
        django_mpp = DjangoMPParser(self.view.request.META, stream, upload_handlers)
        data, files = django_mpp.parse()

        # Flatening data, files and combining them
        data = self.flatten_data(dict(data.iterlists()))
        files = self.flatten_data(dict(files.iterlists()))

        # Strip any parameters that we are treating as reserved
        for key in data.keys():
            if key in self.RESERVED_FORM_PARAMS:
                data.pop(key)
        
        return MultipartData(data, files)
