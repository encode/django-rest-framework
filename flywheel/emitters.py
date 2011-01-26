from django.template import RequestContext, loader

from flywheel.response import NoContent

from utils import dict2xml
try:
    import json
except ImportError:
    import simplejson as json



class BaseEmitter(object):
    media_type = None

    def __init__(self, resource):
        self.resource = resource

    def emit(self, output=NoContent, verbose=False):
        if output is NoContent:
            return ''
        
        return output

class TemplateEmitter(BaseEmitter):
    media_type = None
    template = None

    def emit(self, output=NoContent, verbose=False):
        if output is NoContent:
            return ''

        return self.template.render(Context(output))
        

from django import forms
class JSONForm(forms.Form):
    _contenttype = forms.CharField(max_length=256, initial='application/json', label='Content Type')
    _content = forms.CharField(label='Content', widget=forms.Textarea)

class DocumentingTemplateEmitter(BaseEmitter):
    """Emitter used to self-document the API"""
    template = None

    def emit(self, output=NoContent):
        resource = self.resource

        # Find the first valid emitter and emit the content. (Don't another documenting emitter.)
        emitters = [emitter for emitter in resource.emitters if not isinstance(emitter, DocumentingTemplateEmitter)]
        if not emitters:
            content = 'No emitters were found'
        else:
            content = emitters[0](resource).emit(output, verbose=True)

        # Get the form instance if we have one bound to the input
        form_instance = resource.form_instance
        
        # Otherwise if this isn't an error response
        # then attempt to get a form bound to the response object
        if not form_instance and not resource.response.is_error and resource.response.has_content_body:
            try:
                form_instance = resource.get_form(resource.response.raw_content)
            except:
                pass
        
        # If we still don't have a form instance then try to get an unbound form
        if not form_instance:
            try:
                form_instance = self.resource.get_form()
            except:
                pass

        if not form_instance:
            form_instance = JSONForm()

        template = loader.get_template(self.template)
        context = RequestContext(self.resource.request, {
            'content': content,
            'resource': self.resource,
            'request': self.resource.request,
            'response': self.resource.response,
            'form': form_instance
        })
        
        ret = template.render(context)

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include the normal deletion response code in the output)
        if self.resource.response.status == 204:
            self.resource.response.status = 200

        return ret


class JSONEmitter(BaseEmitter):
    media_type = 'application/json'

    def emit(self, output=NoContent, verbose=False):
        if output is NoContent:
            return ''
        if verbose:
            return json.dumps(output, indent=4, sort_keys=True)
        return json.dumps(output)


class XMLEmitter(BaseEmitter):
    media_type = 'application/xml'

    def emit(self, output=NoContent, verbose=False):
        if output is NoContent:
            return ''
        return dict2xml(output)


class DocumentingHTMLEmitter(DocumentingTemplateEmitter):
    media_type = 'text/html'
    uses_forms = True
    template = 'emitter.html'


class DocumentingXHTMLEmitter(DocumentingTemplateEmitter):
    media_type = 'application/xhtml+xml'
    uses_forms = True
    template = 'emitter.html'


class DocumentingPlainTextEmitter(DocumentingTemplateEmitter):
    media_type = 'text/plain'
    template = 'emitter.txt'


