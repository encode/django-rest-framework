from django.conf import settings
from django.template import RequestContext, loader
from django import forms

from flywheel.response import NoContent

from utils import dict2xml, url_resolves
import string
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
        



class DocumentingTemplateEmitter(BaseEmitter):
    """Emitter used to self-document the API"""
    template = None

    def _get_content(self, resource, output):
        """Get the content as if it had been emitted by a non-documenting emitter.

        (Typically this will be the content as it would have been if the Resource had been
        requested with an 'Accept: */*' header, although with verbose style formatting if appropriate.)"""

        # Find the first valid emitter and emit the content. (Don't use another documenting emitter.)
        emitters = [emitter for emitter in resource.emitters if not isinstance(emitter, DocumentingTemplateEmitter)]
        if not emitters:
            return '[No emitters were found]'
        
        content = emitters[0](resource).emit(output, verbose=True)
        if not all(char in string.printable for char in content):
            return '[%d bytes of binary content]'
            
        return content
            

    def _get_form_instance(self, resource):
        # Get the form instance if we have one bound to the input
        form_instance = resource.form_instance
        
        # Otherwise if this isn't an error response
        # then attempt to get a form bound to the response object
        if not form_instance and resource.response.has_content_body:
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

        # If we still don't have a form instance then try to get an unbound form which can tunnel arbitrary content types
        if not form_instance:
            form_instance = self._get_generic_content_form(resource)
        
        return form_instance


    def _get_generic_content_form(self, resource):
        """Returns a form that allows for arbitrary content types to be tunneled via standard HTML forms
        (Which are typically application/x-www-form-urlencoded)"""

        # NB. http://jacobian.org/writing/dynamic-form-generation/
        class GenericContentForm(forms.Form):
            def __init__(self, resource):
                """We don't know the names of the fields we want to set until the point the form is instantiated,
                as they are determined by the Resource the form is being created against.
                Add the fields dynamically."""
                super(GenericContentForm, self).__init__()

                contenttype_choices = [(media_type, media_type) for media_type in resource.parsed_media_types]
                initial_contenttype = resource.default_parser.media_type

                self.fields[resource.CONTENTTYPE_PARAM] = forms.ChoiceField(label='Content Type',
                                                                            choices=contenttype_choices,
                                                                            initial=initial_contenttype)
                self.fields[resource.CONTENT_PARAM] = forms.CharField(label='Content',
                                                                      widget=forms.Textarea)

        # If either of these reserved parameters are turned off then content tunneling is not possible
        if self.resource.CONTENTTYPE_PARAM is None or self.resource.CONTENT_PARAM is None:
            return None

        # Okey doke, let's do it
        return GenericContentForm(resource)


    def emit(self, output=NoContent):
        content = self._get_content(self.resource, output)
        form_instance = self._get_form_instance(self.resource)

        if url_resolves(settings.LOGIN_URL) and url_resolves(settings.LOGOUT_URL):
            login_url = "%s?next=%s" % (settings.LOGIN_URL, self.resource.request.path)
            logout_url = "%s?next=%s" % (settings.LOGOUT_URL, self.resource.request.path)
        else:
            login_url = None
            logout_url = None

        template = loader.get_template(self.template)
        context = RequestContext(self.resource.request, {
            'content': content,
            'resource': self.resource,
            'request': self.resource.request,
            'response': self.resource.response,
            'form': form_instance,
            'login_url': login_url,
            'logout_url': logout_url,
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


