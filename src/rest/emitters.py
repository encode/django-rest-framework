from django.template import RequestContext, loader
from django.core.handlers.wsgi import STATUS_CODE_TEXT
import json
from utils import dict2xml

class BaseEmitter(object):
    def __init__(self, resource, request, status, headers):
        self.request = request
        self.resource = resource
        self.status = status
        self.headers = headers
    
    def emit(self, output):
        return output

class TemplatedEmitter(BaseEmitter):
    template = None

    def emit(self, output):
        content = json.dumps(output, indent=4)
        template = loader.get_template(self.template)
        context = RequestContext(self.request, {
            'content': content,
            'status': self.status,
            'reason': STATUS_CODE_TEXT.get(self.status, ''),
            'headers': self.headers,
            'resource_name': self.resource.__class__.__name__,
            'resource_doc': self.resource.__doc__,
            'create_form': self.resource.create_form and self.resource.create_form() or None,
            'update_form': self.resource.update_form and self.resource.update_form() or None,
            'allowed_methods': self.resource.allowed_methods,
            'request': self.request,
            'resource': self.resource,
        })
        return template.render(context)
    
class JSONEmitter(BaseEmitter):
    def emit(self, output):
        return json.dumps(output)

class XMLEmitter(BaseEmitter):
    def emit(self, output):
        return dict2xml(output)

class HTMLEmitter(TemplatedEmitter):
    template = 'emitter.html'

class TextEmitter(TemplatedEmitter):
    template = 'emitter.txt'


