from django.template import RequestContext, loader
import json
from utils import dict2xml

class BaseEmitter(object):
    uses_forms = False

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
            'resource': self.resource,
        })
        
        ret = template.render(context)

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include the normal deletion response code in the output)
        if self.resource.resp_status == 204:
            self.resource.resp_status = 200

        return ret

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
    uses_forms = True

class TextEmitter(TemplatedEmitter):
    template = 'emitter.txt'


