"""
Renderers are used to serialize a View's output into specific media types.

Django REST framework also provides HTML and PlainText renderers that help self-document the API,
by serializing the output along with documentation regarding the View, output status and headers,
and providing forms and links depending on the allowed methods, renderers and parsers on the View.
"""
from django import forms
from django.conf import settings
from django.core.serializers.json import DateTimeAwareJSONEncoder
from django.template import RequestContext, loader
from django.utils import simplejson as json


from djangorestframework.compat import yaml
from djangorestframework.utils import dict2xml, url_resolves
from djangorestframework.utils.breadcrumbs import get_breadcrumbs
from djangorestframework.utils.mediatypes import get_media_type_params, add_media_type_param, media_type_matches
from djangorestframework import VERSION

import string
from urllib import quote_plus

__all__ = (
    'BaseRenderer',
    'TemplateRenderer',
    'JSONRenderer',
    'JSONPRenderer',
    'DocumentingHTMLRenderer',
    'DocumentingXHTMLRenderer',
    'DocumentingPlainTextRenderer',
    'XMLRenderer',
    'YAMLRenderer'
)


class BaseRenderer(object):
    """
    All renderers must extend this class, set the :attr:`media_type` attribute,
    and override the :meth:`render` method.
    """

    _FORMAT_QUERY_PARAM = 'format'

    media_type = None
    format = None

    def __init__(self, view):
        self.view = view

    def can_handle_response(self, accept):
        """
        Returns :const:`True` if this renderer is able to deal with the given
        *accept* media type.

        The default implementation for this function is to check the *accept*
        argument against the :attr:`media_type` attribute set on the class to see if
        they match.

        This may be overridden to provide for other behavior, but typically you'll
        instead want to just set the :attr:`media_type` attribute on the class.
        """
        format = self.view.kwargs.get(self._FORMAT_QUERY_PARAM, None)
        if format is None:
            format = self.view.request.GET.get(self._FORMAT_QUERY_PARAM, None)
        if format is not None:
            return format == self.format
        return media_type_matches(self.media_type, accept)

    def render(self, obj=None, media_type=None):
        """
        Given an object render it into a string.

        The requested media type is also passed to this method,
        as it may contain parameters relevant to how the parser
        should render the output.
        EG: ``application/json; indent=4``

        By default render simply returns the output as-is.
        Override this method to provide for other behavior.
        """
        if obj is None:
            return ''

        return str(obj)


class JSONRenderer(BaseRenderer):
    """
    Renderer which serializes to JSON
    """

    media_type = 'application/json'
    format = 'json'

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* into serialized JSON.
        """
        if obj is None:
            return ''

        # If the media type looks like 'application/json; indent=4', then
        # pretty print the result.
        indent = get_media_type_params(media_type).get('indent', None)
        sort_keys = False
        try:
            indent = max(min(int(indent), 8), 0)
            sort_keys = True
        except (ValueError, TypeError):
            indent = None

        return json.dumps(obj, cls=DateTimeAwareJSONEncoder, indent=indent, sort_keys=sort_keys)


class JSONPRenderer(JSONRenderer):
    """
    Renderer which serializes to JSONP
    """

    media_type = 'application/json-p'
    format = 'json-p'
    renderer_class = JSONRenderer
    callback_parameter = 'callback'

    def _get_callback(self):
        return self.view.request.GET.get(self.callback_parameter, self.callback_parameter)

    def _get_renderer(self):
        return self.renderer_class(self.view)

    def render(self, obj=None, media_type=None):
        callback = self._get_callback()
        json = self._get_renderer().render(obj, media_type)
        return "%s(%s);" % (callback, json)


class XMLRenderer(BaseRenderer):
    """
    Renderer which serializes to XML.
    """

    media_type = 'application/xml'
    format = 'xml'

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* into serialized XML.
        """
        if obj is None:
            return ''
        return dict2xml(obj)


if yaml:
    class YAMLRenderer(BaseRenderer):
        """
        Renderer which serializes to YAML.
        """

        media_type = 'application/yaml'
        format = 'yaml'

        def render(self, obj=None, media_type=None):
            """
            Renders *obj* into serialized YAML.
            """
            if obj is None:
                return ''

            return yaml.safe_dump(obj)
else:
    YAMLRenderer = None


class TemplateRenderer(BaseRenderer):
    """
    A Base class provided for convenience.

    Render the object simply by using the given template.
    To create a template renderer, subclass this class, and set
    the :attr:`media_type` and :attr:`template` attributes.
    """

    media_type = None
    template = None

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* using the :attr:`template` specified on the class.
        """
        if obj is None:
            return ''

        template = loader.get_template(self.template)
        context = RequestContext(self.view.request, {'object': obj})
        return template.render(context)


class DocumentingTemplateRenderer(BaseRenderer):
    """
    Base class for renderers used to self-document the API.
    Implementing classes should extend this class and set the template attribute.
    """

    template = None

    def _get_content(self, view, request, obj, media_type):
        """
        Get the content as if it had been rendered by a non-documenting renderer.

        (Typically this will be the content as it would have been if the Resource had been
        requested with an 'Accept: */*' header, although with verbose style formatting if appropriate.)
        """

        # Find the first valid renderer and render the content. (Don't use another documenting renderer.)
        renderers = [renderer for renderer in view.renderers if not issubclass(renderer, DocumentingTemplateRenderer)]
        if not renderers:
            return '[No renderers were found]'

        media_type = add_media_type_param(media_type, 'indent', '4')
        content = renderers[0](view).render(obj, media_type)
        if not all(char in string.printable for char in content):
            return '[%d bytes of binary content]'

        return content

    def _get_form_instance(self, view, method):
        """
        Get a form, possibly bound to either the input or output data.
        In the absence on of the Resource having an associated form then
        provide a form that can be used to submit arbitrary content.
        """

        # Get the form instance if we have one bound to the input
        form_instance = None
        if method == getattr(view, 'method', view.request.method).lower():
            form_instance = getattr(view, 'bound_form_instance', None)

        if not form_instance and hasattr(view, 'get_bound_form'):
            # Otherwise if we have a response that is valid against the form then use that
            if view.response.has_content_body:
                try:
                    form_instance = view.get_bound_form(view.response.cleaned_content, method=method)
                    if form_instance and not form_instance.is_valid():
                        form_instance = None
                except Exception:
                    form_instance = None

        # If we still don't have a form instance then try to get an unbound form
        if not form_instance:
            try:
                form_instance = view.get_bound_form(method=method)
            except Exception:
                pass

        # If we still don't have a form instance then try to get an unbound form which can tunnel arbitrary content types
        if not form_instance:
            form_instance = self._get_generic_content_form(view)

        return form_instance

    def _get_generic_content_form(self, view):
        """
        Returns a form that allows for arbitrary content types to be tunneled via standard HTML forms
        (Which are typically application/x-www-form-urlencoded)
        """

        # If we're not using content overloading there's no point in supplying a generic form,
        # as the view won't treat the form's value as the content of the request.
        if not getattr(view, '_USE_FORM_OVERLOADING', False):
            return None

        # NB. http://jacobian.org/writing/dynamic-form-generation/
        class GenericContentForm(forms.Form):
            def __init__(self, view):
                """We don't know the names of the fields we want to set until the point the form is instantiated,
                as they are determined by the Resource the form is being created against.
                Add the fields dynamically."""
                super(GenericContentForm, self).__init__()

                contenttype_choices = [(media_type, media_type) for media_type in view._parsed_media_types]
                initial_contenttype = view._default_parser.media_type

                self.fields[view._CONTENTTYPE_PARAM] = forms.ChoiceField(label='Content Type',
                                                                         choices=contenttype_choices,
                                                                         initial=initial_contenttype)
                self.fields[view._CONTENT_PARAM] = forms.CharField(label='Content',
                                                                   widget=forms.Textarea)

        # If either of these reserved parameters are turned off then content tunneling is not possible
        if self.view._CONTENTTYPE_PARAM is None or self.view._CONTENT_PARAM is None:
            return None

        # Okey doke, let's do it
        return GenericContentForm(view)

    def get_name(self):
        try:
            return self.view.get_name()
        except AttributeError:
            return self.view.__doc__

    def get_description(self, html=None):
        if html is None:
            html = bool('html' in self.format)
        try:
            return self.view.get_description(html)
        except AttributeError:
            return self.view.__doc__

    def render(self, obj=None, media_type=None):
        """
        Renders *obj* using the :attr:`template` set on the class.

        The context used in the template contains all the information
        needed to self-document the response to this request.
        """

        content = self._get_content(self.view, self.view.request, obj, media_type)

        put_form_instance = self._get_form_instance(self.view, 'put')
        post_form_instance = self._get_form_instance(self.view, 'post')

        if url_resolves(settings.LOGIN_URL) and url_resolves(settings.LOGOUT_URL):
            login_url = "%s?next=%s" % (settings.LOGIN_URL, quote_plus(self.view.request.path))
            logout_url = "%s?next=%s" % (settings.LOGOUT_URL, quote_plus(self.view.request.path))
        else:
            login_url = None
            logout_url = None

        name = self.get_name()
        description = self.get_description()

        breadcrumb_list = get_breadcrumbs(self.view.request.path)

        template = loader.get_template(self.template)
        context = RequestContext(self.view.request, {
            'content': content,
            'view': self.view,
            'request': self.view.request,  # TODO: remove
            'response': self.view.response,
            'description': description,
            'name': name,
            'version': VERSION,
            'breadcrumblist': breadcrumb_list,
            'available_formats': self.view._rendered_formats,
            'put_form': put_form_instance,
            'post_form': post_form_instance,
            'login_url': login_url,
            'logout_url': logout_url,
            'FORMAT_PARAM': self._FORMAT_QUERY_PARAM,
            'METHOD_PARAM': getattr(self.view, '_METHOD_PARAM', None),
            'ADMIN_MEDIA_PREFIX': getattr(settings, 'ADMIN_MEDIA_PREFIX', None),
        })

        ret = template.render(context)

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include
        # the normal deletion response code in the output)
        if self.view.response.status == 204:
            self.view.response.status = 200

        return ret


class DocumentingHTMLRenderer(DocumentingTemplateRenderer):
    """
    Renderer which provides a browsable HTML interface for an API.
    See the examples at http://api.django-rest-framework.org to see this in action.
    """

    media_type = 'text/html'
    format = 'html'
    template = 'renderer.html'


class DocumentingXHTMLRenderer(DocumentingTemplateRenderer):
    """
    Identical to DocumentingHTMLRenderer, except with an xhtml media type.
    We need this to be listed in preference to xml in order to return HTML to WebKit based browsers,
    given their Accept headers.
    """

    media_type = 'application/xhtml+xml'
    format = 'xhtml'
    template = 'renderer.html'


class DocumentingPlainTextRenderer(DocumentingTemplateRenderer):
    """
    Renderer that serializes the object with the default renderer, but also provides plain-text
    documentation of the returned status and headers, and of the resource's name and description.
    Useful for browsing an API with command line tools.
    """

    media_type = 'text/plain'
    format = 'txt'
    template = 'renderer.txt'


DEFAULT_RENDERERS = (
    JSONRenderer,
    JSONPRenderer,
    DocumentingHTMLRenderer,
    DocumentingXHTMLRenderer,
    DocumentingPlainTextRenderer,
    XMLRenderer
)

if YAMLRenderer:
    DEFAULT_RENDERERS += (YAMLRenderer,)
