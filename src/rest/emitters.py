from django.template import RequestContext, loader
from django.core.handlers.wsgi import STATUS_CODE_TEXT
import json
from utils import dict2xml

class BaseEmitter(object):
    def __init__(self, resource):
        self.resource = resource

    def emit(self, output):
        return output

class TemplatedEmitter(BaseEmitter):
    template = None

    def emit(self, output):
        if output is None:
            content = ''
        else:
            content = json.dumps(output, indent=4, sort_keys=True)

        template = loader.get_template(self.template)
        context = RequestContext(self.resource.request, {
            'content': content,
            'status': self.resource.resp_status,
            'reason': STATUS_CODE_TEXT.get(self.resource.resp_status, ''),
            'headers': self.resource.resp_headers,
            'resource_name': self.resource.__class__.__name__,
            'resource_doc': self.resource.__doc__,
            'create_form': self.resource.form,
            'update_form': self.resource.form,
            'request': self.resource.request,
            'resource': self.resource,
        })
        
        # Munge DELETE Response code to allow us to return content
        if self.resource.resp_status == 204:
            self.resource.resp_status = 200

        return template.render(context)

class JSONEmitter(BaseEmitter):
    def emit(self, output):
        if output is None:
            # Treat None as no message body, rather than serializing
            return ''
        return json.dumps(output)

class XMLEmitter(BaseEmitter):
    def emit(self, output):
        if output is None:
            # Treat None as no message body, rather than serializing
            return ''
        return dict2xml(output)

class HTMLEmitter(TemplatedEmitter):
    template = 'emitter.html'

class TextEmitter(TemplatedEmitter):
    template = 'emitter.txt'


