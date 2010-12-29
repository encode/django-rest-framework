class BaseParser(object):
    def __init__(self, resource, request):
        self.resource = resource
        self.request = request
    
    def parse(self, input):
        return {}


class JSONParser(BaseParser):
    pass

class XMLParser(BaseParser):
    pass

class FormParser(BaseParser):
    pass

