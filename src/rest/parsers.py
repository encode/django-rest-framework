import json

class BaseParser(object):
    def __init__(self, resource):
        self.resource = resource
    
    def parse(self, input):
        return {}


class JSONParser(BaseParser):
    def parse(self, input):
        return json.loads(input)

class XMLParser(BaseParser):
    pass

class FormParser(BaseParser):
    """The default parser for form data.
    Return a dict containing a single value for each non-reserved parameter
    """
    def __init__(self, resource):

        if resource.request.method == 'PUT':
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
            if hasattr(resource.request, '_post'):
                del request._post
                del request._files
            
            try:
                resource.request.method = "POST"
                resource.request._load_post_and_files()
                resource.request.method = "PUT"
            except AttributeError:
                resource.request.META['REQUEST_METHOD'] = 'POST'
                resource.request._load_post_and_files()
                resource.request.META['REQUEST_METHOD'] = 'PUT'

        # 
        self.data = {}
        for (key, val) in resource.request.POST.items():
            if key not in resource.RESERVED_PARAMS:
                self.data[key] = val

    def parse(self, input):
        return self.data

