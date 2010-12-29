from django.template import Context, loader
import json

class BaseEmitter(object):
    def __init__(self, resource, status, headers):
        self.resource = resource
        self.status = status
        self.headers = headers
    
    def emit(self, output):
        return output

class TemplatedEmitter(BaseEmitter):
    def emit(self, output):
        content = json.dumps(output, indent=4)
        template = loader.get_template(self.template)
        context = Context({
            'content': content,
            'status': self.status,
            'headers': self.headers,
            'resource_name': self.resource.__class__.__name__,
            'resource_doc': self.resource.__doc__
        })
        return template.render(context)
    
class JSONEmitter(BaseEmitter):
    def emit(self, output):
        return json.dumps(output)

class XMLEmitter(BaseEmitter):
    pass

class HTMLEmitter(TemplatedEmitter):
    template = 'emitter.html'

class TextEmitter(TemplatedEmitter):
    template = 'emitter.txt'


