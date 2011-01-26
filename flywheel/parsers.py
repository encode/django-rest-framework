from flywheel.response import status, ResponseException

try:
    import json
except ImportError:
    import simplejson as json

# TODO: Make all parsers only list a single media_type, rather than a list

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
    
    media_type = 'application/x-www-form-urlencoded'

    def parse(self, input):
        # The FormParser doesn't parse the input as other parsers would, since Django's already done the
        # form parsing for us.  We build the content object from the request directly.
        request = self.resource.request

        if request.method == 'PUT':
            # Fix from piston to force Django to give PUT requests the same
            # form processing that POST requests get...
            #
            # Bug fix: if _load_post_and_files has already been called, for
            # example by middleware accessing request.POST, the below code to
            # pretend the request is a POST instead of a PUT will be too late
            # to make a difference. Also calling _load_post_and_files will result 
            # in the following exception:
            #   AttributeError: You cannot set the upload handlers after the upload has been processed.
            # The fix is to check for the presence of the _post field which is set 
            # the first time _load_post_and_files is called (both by wsgi.py and 
            # modpython.py). If it's set, the request has to be 'reset' to redo
            # the query value parsing in POST mode.
            if hasattr(request, '_post'):
                del request._post
                del request._files
            
            try:
                request.method = "POST"
                request._load_post_and_files()
                request.method = "PUT"
            except AttributeError:
                request.META['REQUEST_METHOD'] = 'POST'
                request._load_post_and_files()
                request.META['REQUEST_METHOD'] = 'PUT'

        # Strip any parameters that we are treating as reserved
        data = {}
        for (key, val) in request.POST.items():
            if key not in self.resource.RESERVED_FORM_PARAMS:
                data[key] = val
        
        return data


