import json

class BaseParser(object):
    def __init__(self, resource, request):
        self.resource = resource
        self.request = request
    
    def parse(self, input):
        return {}


class JSONParser(BaseParser):
    def parse(self, input):
        return json.loads(input)

class XMLParser(BaseParser):
    pass

class FormParser(BaseParser):
    def parse(self, input):
        return self.request.POST

