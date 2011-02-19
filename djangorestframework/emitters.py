"""Emitters are used to serialize a Resource's output into specific media types.
django-rest-framework also provides HTML and PlainText emitters that help self-document the API,
by serializing the output along with documentation regarding the Resource, output status and headers,
and providing forms and links depending on the allowed methods, emitters and parsers on the Resource. 
"""
from django.conf import settings
from django.http import HttpResponse
from django.template import RequestContext, loader
from django import forms

from djangorestframework.response import NoContent, ResponseException
from djangorestframework.validators import FormValidatorMixin
from djangorestframework.utils import dict2xml, url_resolves
from djangorestframework.markdownwrapper import apply_markdown
from djangorestframework.breadcrumbs import get_breadcrumbs
from djangorestframework.content import OverloadedContentMixin
from djangorestframework.description import get_name, get_description
from djangorestframework import status

from urllib import quote_plus
import string
import re
from decimal import Decimal

try:
    import json
except ImportError:
    import simplejson as json


_MSIE_USER_AGENT = re.compile(r'^Mozilla/[0-9]+\.[0-9]+ \([^)]*; MSIE [0-9]+\.[0-9]+[a-z]?;[^)]*\)(?!.* Opera )')


class EmitterMixin(object):
    """Adds behaviour for pluggable Emitters to a :class:`.Resource` or Django :class:`View`. class.
    
    Default behaviour is to use standard HTTP Accept header content negotiation.
    Also supports overidding the content type by specifying an _accept= parameter in the URL.
    Ignores Accept headers from Internet Explorer user agents and uses a sensible browser Accept header instead."""

    ACCEPT_QUERY_PARAM = '_accept'        # Allow override of Accept header in URL query params
    REWRITE_IE_ACCEPT_HEADER = True

    request = None
    response = None
    emitters = ()

    def emit(self, response):
        """Takes a :class:`Response` object and returns a Django :class:`HttpResponse`."""
        self.response = response

        try:
            emitter = self._determine_emitter(self.request)
        except ResponseException, exc:
            emitter = self.default_emitter
            response = exc.response
        
        # Serialize the response content
        if response.has_content_body:
            content = emitter(self).emit(output=response.cleaned_content)
        else:
            content = emitter(self).emit()
        
        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include the normal deletion response code in the output)
        if response.status == 204:
            response.status = 200
        
        # Build the HTTP Response
        # TODO: Check if emitter.mimetype is underspecified, or if a content-type header has been set
        resp = HttpResponse(content, mimetype=emitter.media_type, status=response.status)
        for (key, val) in response.headers.items():
            resp[key] = val

        return resp


    def _determine_emitter(self, request):
        """Return the appropriate emitter for the output, given the client's 'Accept' header,
        and the content types that this Resource knows how to serve.
        
        See: RFC 2616, Section 14 - http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html"""

        if self.ACCEPT_QUERY_PARAM and request.GET.get(self.ACCEPT_QUERY_PARAM, None):
            # Use _accept parameter override
            accept_list = [request.GET.get(self.ACCEPT_QUERY_PARAM)]
        elif self.REWRITE_IE_ACCEPT_HEADER and request.META.has_key('HTTP_USER_AGENT') and _MSIE_USER_AGENT.match(request.META['HTTP_USER_AGENT']):
            accept_list = ['text/html', '*/*']
        elif request.META.has_key('HTTP_ACCEPT'):
            # Use standard HTTP Accept negotiation
            accept_list = request.META["HTTP_ACCEPT"].split(',')
        else:
            # No accept header specified
            return self.default_emitter
        
        # Parse the accept header into a dict of {qvalue: set of media types}
        # We ignore mietype parameters
        accept_dict = {}    
        for token in accept_list:
            components = token.split(';')
            mimetype = components[0].strip()
            qvalue = Decimal('1.0')
            
            if len(components) > 1:
                # Parse items that have a qvalue eg text/html;q=0.9
                try:
                    (q, num) = components[-1].split('=')
                    if q == 'q':
                        qvalue = Decimal(num)
                except:
                    # Skip malformed entries
                    continue

            if accept_dict.has_key(qvalue):
                accept_dict[qvalue].add(mimetype)
            else:
                accept_dict[qvalue] = set((mimetype,))
        
        # Convert to a list of sets ordered by qvalue (highest first)
        accept_sets = [accept_dict[qvalue] for qvalue in sorted(accept_dict.keys(), reverse=True)]
       
        for accept_set in accept_sets:
            # Return any exact match
            for emitter in self.emitters:
                if emitter.media_type in accept_set:
                    return emitter

            # Return any subtype match
            for emitter in self.emitters:
                if emitter.media_type.split('/')[0] + '/*' in accept_set:
                    return emitter

            # Return default
            if '*/*' in accept_set:
                return self.default_emitter
      

        raise ResponseException(status.HTTP_406_NOT_ACCEPTABLE,
                                {'detail': 'Could not statisfy the client\'s Accept header',
                                 'available_types': self.emitted_media_types})

    @property
    def emitted_media_types(self):
        """Return an list of all the media types that this resource can emit."""
        return [emitter.media_type for emitter in self.emitters]

    @property
    def default_emitter(self):
        """Return the resource's most prefered emitter.
        (This emitter is used if the client does not send and Accept: header, or sends Accept: */*)"""
        return self.emitters[0]



# TODO: Rename verbose to something more appropriate
# TODO: NoContent could be handled more cleanly.  It'd be nice if it was handled by default,
#       and only have an emitter output anything if it explicitly provides support for that.

class BaseEmitter(object):
    """All emitters must extend this class, set the media_type attribute, and
    override the emit() function."""
    media_type = None

    def __init__(self, resource):
        self.resource = resource

    def emit(self, output=NoContent, verbose=False):
        """By default emit simply returns the ouput as-is.
        Override this method to provide for other behaviour."""
        if output is NoContent:
            return ''
        
        return output


class TemplateEmitter(BaseEmitter):
    """Provided for convienience.
    Emit the output by simply rendering it with the given template."""
    media_type = None
    template = None

    def emit(self, output=NoContent, verbose=False):
        if output is NoContent:
            return ''

        context = RequestContext(self.request, output)
        return self.template.render(context)


class DocumentingTemplateEmitter(BaseEmitter):
    """Base class for emitters used to self-document the API.
    Implementing classes should extend this class and set the template attribute."""
    template = None

    def _get_content(self, resource, request, output):
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
        """Get a form, possibly bound to either the input or output data.
        In the absence on of the Resource having an associated form then
        provide a form that can be used to submit arbitrary content."""
        # Get the form instance if we have one bound to the input
        #form_instance = resource.form_instance
        # TODO! Reinstate this

        form_instance = None

        if isinstance(resource, FormValidatorMixin):
            # If we already have a bound form instance (IE provided by the input parser, then use that)
            if resource.bound_form_instance is not None:
                form_instance = resource.bound_form_instance
                
            # Otherwise if we have a response that is valid against the form then use that
            if not form_instance and resource.response.has_content_body:
                try:
                    form_instance = resource.get_bound_form(resource.response.raw_content)
                    if form_instance and not form_instance.is_valid():
                        form_instance = None
                except:
                    form_instance = None
            
            # If we still don't have a form instance then try to get an unbound form
            if not form_instance:
                try:
                    form_instance = resource.get_bound_form()
                except:
                    pass

        # If we still don't have a form instance then try to get an unbound form which can tunnel arbitrary content types
        if not form_instance:
            form_instance = self._get_generic_content_form(resource)
        
        return form_instance


    def _get_generic_content_form(self, resource):
        """Returns a form that allows for arbitrary content types to be tunneled via standard HTML forms
        (Which are typically application/x-www-form-urlencoded)"""

        # If we're not using content overloading there's no point in supplying a generic form,
        # as the resource won't treat the form's value as the content of the request.
        if not isinstance(resource, OverloadedContentMixin):
            return None

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
        content = self._get_content(self.resource, self.resource.request, output)
        form_instance = self._get_form_instance(self.resource)

        if url_resolves(settings.LOGIN_URL) and url_resolves(settings.LOGOUT_URL):
            login_url = "%s?next=%s" % (settings.LOGIN_URL, quote_plus(self.resource.request.path))
            logout_url = "%s?next=%s" % (settings.LOGOUT_URL, quote_plus(self.resource.request.path))
        else:
            login_url = None
            logout_url = None

        name = get_name(self.resource)
        description = get_description(self.resource)

        markeddown = None
        if apply_markdown:
            try:
                markeddown = apply_markdown(description)
            except AttributeError:  # TODO: possibly split the get_description / get_name into a mixin class
                markeddown = None

        breadcrumb_list = get_breadcrumbs(self.resource.request.path)

        template = loader.get_template(self.template)
        context = RequestContext(self.resource.request, {
            'content': content,
            'resource': self.resource,
            'request': self.resource.request,
            'response': self.resource.response,
            'description': description,
            'name': name,
            'markeddown': markeddown,
            'breadcrumblist': breadcrumb_list,
            'form': form_instance,
            'login_url': login_url,
            'logout_url': logout_url,
            'ADMIN_MEDIA_PREFIX': settings.ADMIN_MEDIA_PREFIX
        })
        
        ret = template.render(context)

        return ret


class JSONEmitter(BaseEmitter):
    """Emitter which serializes to JSON"""
    media_type = 'application/json'

    def emit(self, output=NoContent, verbose=False):
        if output is NoContent:
            return ''
        if verbose:
            return json.dumps(output, indent=4, sort_keys=True)
        return json.dumps(output)


class XMLEmitter(BaseEmitter):
    """Emitter which serializes to XML."""
    media_type = 'application/xml'

    def emit(self, output=NoContent, verbose=False):
        if output is NoContent:
            return ''
        return dict2xml(output)


class DocumentingHTMLEmitter(DocumentingTemplateEmitter):
    """Emitter which provides a browsable HTML interface for an API.
    See the examples listed in the django-rest-framework documentation to see this in actions."""
    media_type = 'text/html'
    template = 'emitter.html'


class DocumentingXHTMLEmitter(DocumentingTemplateEmitter):
    """Identical to DocumentingHTMLEmitter, except with an xhtml media type.
    We need this to be listed in preference to xml in order to return HTML to WebKit based browsers,
    given their Accept headers."""
    media_type = 'application/xhtml+xml'
    template = 'emitter.html'


class DocumentingPlainTextEmitter(DocumentingTemplateEmitter):
    """Emitter that serializes the output with the default emitter, but also provides plain-text
    doumentation of the returned status and headers, and of the resource's name and description.
    Useful for browsing an API with command line tools."""
    media_type = 'text/plain'
    template = 'emitter.txt'
    
DEFAULT_EMITTERS = ( JSONEmitter,
                     DocumentingHTMLEmitter,
                     DocumentingXHTMLEmitter,
                     DocumentingPlainTextEmitter,
                     XMLEmitter )


