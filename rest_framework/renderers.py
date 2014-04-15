"""
Renderers are used to serialize a response into specific media types.

They give us a generic way of being able to handle various media types
on the response, such as JSON encoded data or HTML output.

REST framework also provides an HTML renderer the renders the browsable API.
"""
from __future__ import unicode_literals

import copy
import json
import django
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.http.multipartparser import parse_header
from django.template import RequestContext, loader, Template
from django.test.client import encode_multipart
from django.utils.xmlutils import SimplerXMLGenerator
from rest_framework.compat import StringIO
from rest_framework.compat import six
from rest_framework.compat import smart_text
from rest_framework.compat import yaml
from rest_framework.exceptions import ParseError
from rest_framework.settings import api_settings
from rest_framework.request import is_form_media_type, override_method
from rest_framework.utils import encoders
from rest_framework.utils.breadcrumbs import get_breadcrumbs
from rest_framework import exceptions, status, VERSION


class BaseRenderer(object):
    """
    All renderers should extend this class, setting the `media_type`
    and `format` attributes, and override the `.render()` method.
    """

    media_type = None
    format = None
    charset = 'utf-8'
    render_style = 'text'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        raise NotImplemented('Renderer class requires .render() to be implemented')


class JSONRenderer(BaseRenderer):
    """
    Renderer which serializes to JSON.
    Applies JSON's backslash-u character escaping for non-ascii characters.
    """

    media_type = 'application/json'
    format = 'json'
    encoder_class = encoders.JSONEncoder
    ensure_ascii = True
    charset = None
    # JSON is a binary encoding, that can be encoded as utf-8, utf-16 or utf-32.
    # See: http://www.ietf.org/rfc/rfc4627.txt
    # Also: http://lucumr.pocoo.org/2013/7/19/application-mimetypes-and-encodings/

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON.
        """
        if data is None:
            return bytes()

        # If 'indent' is provided in the context, then pretty print the result.
        # E.g. If we're being called by the BrowsableAPIRenderer.
        renderer_context = renderer_context or {}
        indent = renderer_context.get('indent', None)

        if accepted_media_type:
            # If the media type looks like 'application/json; indent=4',
            # then pretty print the result.
            base_media_type, params = parse_header(accepted_media_type.encode('ascii'))
            indent = params.get('indent', indent)
            try:
                indent = max(min(int(indent), 8), 0)
            except (ValueError, TypeError):
                indent = None

        ret = json.dumps(data, cls=self.encoder_class,
            indent=indent, ensure_ascii=self.ensure_ascii)

        # On python 2.x json.dumps() returns bytestrings if ensure_ascii=True,
        # but if ensure_ascii=False, the return type is underspecified,
        # and may (or may not) be unicode.
        # On python 3.x json.dumps() returns unicode strings.
        if isinstance(ret, six.text_type):
            return bytes(ret.encode('utf-8'))
        return ret


class UnicodeJSONRenderer(JSONRenderer):
    ensure_ascii = False
    """
    Renderer which serializes to JSON.
    Does *not* apply JSON's character escaping for non-ascii characters.
    """


class JSONPRenderer(JSONRenderer):
    """
    Renderer which serializes to json,
    wrapping the json output in a callback function.
    """

    media_type = 'application/javascript'
    format = 'jsonp'
    callback_parameter = 'callback'
    default_callback = 'callback'
    charset = 'utf-8'

    def get_callback(self, renderer_context):
        """
        Determine the name of the callback to wrap around the json output.
        """
        request = renderer_context.get('request', None)
        params = request and request.QUERY_PARAMS or {}
        return params.get(self.callback_parameter, self.default_callback)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders into jsonp, wrapping the json output in a callback function.

        Clients may set the callback function name using a query parameter
        on the URL, for example: ?callback=exampleCallbackName
        """
        renderer_context = renderer_context or {}
        callback = self.get_callback(renderer_context)
        json = super(JSONPRenderer, self).render(data, accepted_media_type,
                                                 renderer_context)
        return callback.encode(self.charset) + b'(' + json + b');'


class XMLRenderer(BaseRenderer):
    """
    Renderer which serializes to XML.
    """

    media_type = 'application/xml'
    format = 'xml'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders `data` into serialized XML.
        """
        if data is None:
            return ''

        stream = StringIO()

        xml = SimplerXMLGenerator(stream, self.charset)
        xml.startDocument()
        xml.startElement("root", {})

        self._to_xml(xml, data)

        xml.endElement("root")
        xml.endDocument()
        return stream.getvalue()

    def _to_xml(self, xml, data):
        if isinstance(data, (list, tuple)):
            for item in data:
                xml.startElement("list-item", {})
                self._to_xml(xml, item)
                xml.endElement("list-item")

        elif isinstance(data, dict):
            for key, value in six.iteritems(data):
                xml.startElement(key, {})
                self._to_xml(xml, value)
                xml.endElement(key)

        elif data is None:
            # Don't output any value
            pass

        else:
            xml.characters(smart_text(data))


class YAMLRenderer(BaseRenderer):
    """
    Renderer which serializes to YAML.
    """

    media_type = 'application/yaml'
    format = 'yaml'
    encoder = encoders.SafeDumper
    charset = 'utf-8'
    ensure_ascii = True

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders `data` into serialized YAML.
        """
        assert yaml, 'YAMLRenderer requires pyyaml to be installed'

        if data is None:
            return ''

        return yaml.dump(data, stream=None, encoding=self.charset, Dumper=self.encoder, allow_unicode=not self.ensure_ascii)


class UnicodeYAMLRenderer(YAMLRenderer):
    """
    Renderer which serializes to YAML.
    Does *not* apply character escaping for non-ascii characters.
    """
    ensure_ascii = False


class TemplateHTMLRenderer(BaseRenderer):
    """
    An HTML renderer for use with templates.

    The data supplied to the Response object should be a dictionary that will
    be used as context for the template.

    The template name is determined by (in order of preference):

    1. An explicit `.template_name` attribute set on the response.
    2. An explicit `.template_name` attribute set on this class.
    3. The return result of calling `view.get_template_names()`.

    For example:
        data = {'users': User.objects.all()}
        return Response(data, template_name='users.html')

    For pre-rendered HTML, see StaticHTMLRenderer.
    """

    media_type = 'text/html'
    format = 'html'
    template_name = None
    exception_template_names = [
        '%(status_code)s.html',
        'api_exception.html'
    ]
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders data to HTML, using Django's standard template rendering.

        The template name is determined by (in order of preference):

        1. An explicit .template_name set on the response.
        2. An explicit .template_name set on this class.
        3. The return result of calling view.get_template_names().
        """
        renderer_context = renderer_context or {}
        view = renderer_context['view']
        request = renderer_context['request']
        response = renderer_context['response']

        if response.exception:
            template = self.get_exception_template(response)
        else:
            template_names = self.get_template_names(response, view)
            template = self.resolve_template(template_names)

        context = self.resolve_context(data, request, response)
        return template.render(context)

    def resolve_template(self, template_names):
        return loader.select_template(template_names)

    def resolve_context(self, data, request, response):
        if response.exception:
            data['status_code'] = response.status_code
        return RequestContext(request, data)

    def get_template_names(self, response, view):
        if response.template_name:
            return [response.template_name]
        elif self.template_name:
            return [self.template_name]
        elif hasattr(view, 'get_template_names'):
            return view.get_template_names()
        elif hasattr(view, 'template_name'):
            return [view.template_name]
        raise ImproperlyConfigured('Returned a template response with no `template_name` attribute set on either the view or response')

    def get_exception_template(self, response):
        template_names = [name % {'status_code': response.status_code}
                          for name in self.exception_template_names]

        try:
            # Try to find an appropriate error template
            return self.resolve_template(template_names)
        except Exception:
            # Fall back to using eg '404 Not Found'
            return Template('%d %s' % (response.status_code,
                                       response.status_text.title()))


# Note, subclass TemplateHTMLRenderer simply for the exception behavior
class StaticHTMLRenderer(TemplateHTMLRenderer):
    """
    An HTML renderer class that simply returns pre-rendered HTML.

    The data supplied to the Response object should be a string representing
    the pre-rendered HTML content.

    For example:
        data = '<html><body>example</body></html>'
        return Response(data)

    For template rendered HTML, see TemplateHTMLRenderer.
    """
    media_type = 'text/html'
    format = 'html'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        renderer_context = renderer_context or {}
        response = renderer_context['response']

        if response and response.exception:
            request = renderer_context['request']
            template = self.get_exception_template(response)
            context = self.resolve_context(data, request, response)
            return template.render(context)

        return data


class HTMLFormRenderer(BaseRenderer):
    """
    Renderers serializer data into an HTML form.

    If the serializer was instantiated without an object then this will
    return an HTML form not bound to any object,
    otherwise it will return an HTML form with the appropriate initial data
    populated from the object.

    Note that rendering of field and form errors is not currently supported.
    """
    media_type = 'text/html'
    format = 'form'
    template = 'rest_framework/form.html'
    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render serializer data and return an HTML form, as a string.
        """
        renderer_context = renderer_context or {}
        request = renderer_context['request']

        template = loader.get_template(self.template)
        context = RequestContext(request, {'form': data})
        return template.render(context)


class BrowsableAPIRenderer(BaseRenderer):
    """
    HTML renderer used to self-document the API.
    """
    media_type = 'text/html'
    format = 'api'
    template = 'rest_framework/api.html'
    charset = 'utf-8'
    form_renderer_class = HTMLFormRenderer

    def get_default_renderer(self, view):
        """
        Return an instance of the first valid renderer.
        (Don't use another documenting renderer.)
        """
        renderers = [renderer for renderer in view.renderer_classes
                     if not issubclass(renderer, BrowsableAPIRenderer)]
        non_template_renderers = [renderer for renderer in renderers
                                  if not hasattr(renderer, 'get_template_names')]

        if not renderers:
            return None
        elif non_template_renderers:
            return non_template_renderers[0]()
        return renderers[0]()

    def get_content(self, renderer, data,
                    accepted_media_type, renderer_context):
        """
        Get the content as if it had been rendered by the default
        non-documenting renderer.
        """
        if not renderer:
            return '[No renderers were found]'

        renderer_context['indent'] = 4
        content = renderer.render(data, accepted_media_type, renderer_context)

        render_style = getattr(renderer, 'render_style', 'text')
        assert render_style in ['text', 'binary'], 'Expected .render_style ' \
            '"text" or "binary", but got "%s"' % render_style
        if render_style == 'binary':
            return '[%d bytes of binary content]' % len(content)

        return content

    def show_form_for_method(self, view, method, request, obj):
        """
        Returns True if a form should be shown for this method.
        """
        if not method in view.allowed_methods:
            return  # Not a valid method

        if not api_settings.FORM_METHOD_OVERRIDE:
            return  # Cannot use form overloading

        try:
            view.check_permissions(request)
            if obj is not None:
                view.check_object_permissions(request, obj)
        except exceptions.APIException:
            return False  # Doesn't have permissions
        return True

    def get_rendered_html_form(self, view, method, request):
        """
        Return a string representing a rendered HTML form, possibly bound to
        either the input or output data.

        In the absence of the View having an associated form then return None.
        """
        if request.method == method:
            try:
                data = request.DATA
                files = request.FILES
            except ParseError:
                data = None
                files = None
        else:
            data = None
            files = None

        with override_method(view, request, method) as request:
            obj = getattr(view, 'object', None)
            if not self.show_form_for_method(view, method, request, obj):
                return

            if method in ('DELETE', 'OPTIONS'):
                return True  # Don't actually need to return a form

            if (not getattr(view, 'get_serializer', None)
                or not any(is_form_media_type(parser.media_type) for parser in view.parser_classes)):
                return

            serializer = view.get_serializer(instance=obj, data=data, files=files)
            serializer.is_valid()
            data = serializer.data

            form_renderer = self.form_renderer_class()
            return form_renderer.render(data, self.accepted_media_type, self.renderer_context)

    def get_raw_data_form(self, view, method, request):
        """
        Returns a form that allows for arbitrary content types to be tunneled
        via standard HTML forms.
        (Which are typically application/x-www-form-urlencoded)
        """
        with override_method(view, request, method) as request:
            # If we're not using content overloading there's no point in
            # supplying a generic form, as the view won't treat the form's
            # value as the content of the request.
            if not (api_settings.FORM_CONTENT_OVERRIDE
                    and api_settings.FORM_CONTENTTYPE_OVERRIDE):
                return None

            # Check permissions
            obj = getattr(view, 'object', None)
            if not self.show_form_for_method(view, method, request, obj):
                return

            # If possible, serialize the initial content for the generic form
            default_parser = view.parser_classes[0]
            renderer_class = getattr(default_parser, 'renderer_class', None)
            if (hasattr(view, 'get_serializer') and renderer_class):
                # View has a serializer defined and parser class has a
                # corresponding renderer that can be used to render the data.

                # Get a read-only version of the serializer
                serializer = view.get_serializer(instance=obj)
                if obj is None:
                    for name, field in serializer.fields.items():
                        if getattr(field, 'read_only', None):
                            del serializer.fields[name]

                # Render the raw data content
                renderer = renderer_class()
                accepted = self.accepted_media_type
                context = self.renderer_context.copy()
                context['indent'] = 4
                content = renderer.render(serializer.data, accepted, context)
            else:
                content = None

            # Generate a generic form that includes a content type field,
            # and a content field.
            content_type_field = api_settings.FORM_CONTENTTYPE_OVERRIDE
            content_field = api_settings.FORM_CONTENT_OVERRIDE

            media_types = [parser.media_type for parser in view.parser_classes]
            choices = [(media_type, media_type) for media_type in media_types]
            initial = media_types[0]

            # NB. http://jacobian.org/writing/dynamic-form-generation/
            class GenericContentForm(forms.Form):
                def __init__(self):
                    super(GenericContentForm, self).__init__()

                    self.fields[content_type_field] = forms.ChoiceField(
                        label='Media type',
                        choices=choices,
                        initial=initial
                    )
                    self.fields[content_field] = forms.CharField(
                        label='Content',
                        widget=forms.Textarea,
                        initial=content
                    )

            return GenericContentForm()

    def get_name(self, view):
        return view.get_view_name()

    def get_description(self, view):
        return view.get_view_description(html=True)

    def get_breadcrumbs(self, request):
        return get_breadcrumbs(request.path)

    def get_context(self, data, accepted_media_type, renderer_context):
        """
        Returns the context used to render.
        """
        view = renderer_context['view']
        request = renderer_context['request']
        response = renderer_context['response']

        renderer = self.get_default_renderer(view)

        raw_data_post_form = self.get_raw_data_form(view, 'POST', request)
        raw_data_put_form = self.get_raw_data_form(view, 'PUT', request)
        raw_data_patch_form = self.get_raw_data_form(view, 'PATCH', request)
        raw_data_put_or_patch_form = raw_data_put_form or raw_data_patch_form

        response_headers = dict(response.items())
        renderer_content_type = ''
        if renderer:
            renderer_content_type = '%s' % renderer.media_type
            if renderer.charset:
                renderer_content_type += ' ;%s' % renderer.charset
        response_headers['Content-Type'] = renderer_content_type

        context = {
            'content': self.get_content(renderer, data, accepted_media_type, renderer_context),
            'view': view,
            'request': request,
            'response': response,
            'description': self.get_description(view),
            'name': self.get_name(view),
            'version': VERSION,
            'breadcrumblist': self.get_breadcrumbs(request),
            'allowed_methods': view.allowed_methods,
            'available_formats': [renderer.format for renderer in view.renderer_classes],
            'response_headers': response_headers,

            'put_form': self.get_rendered_html_form(view, 'PUT', request),
            'post_form': self.get_rendered_html_form(view, 'POST', request),
            'delete_form': self.get_rendered_html_form(view, 'DELETE', request),
            'options_form': self.get_rendered_html_form(view, 'OPTIONS', request),

            'raw_data_put_form': raw_data_put_form,
            'raw_data_post_form': raw_data_post_form,
            'raw_data_patch_form': raw_data_patch_form,
            'raw_data_put_or_patch_form': raw_data_put_or_patch_form,

            'display_edit_forms': bool(response.status_code != 403),

            'api_settings': api_settings
        }
        return context

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the HTML for the browsable API representation.
        """
        self.accepted_media_type = accepted_media_type or ''
        self.renderer_context = renderer_context or {}

        template = loader.get_template(self.template)
        context = self.get_context(data, accepted_media_type, renderer_context)
        context = RequestContext(renderer_context['request'], context)
        ret = template.render(context)

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include
        # the normal deletion response code in the output)
        response = renderer_context['response']
        if response.status_code == status.HTTP_204_NO_CONTENT:
            response.status_code = status.HTTP_200_OK

        return ret


class MultiPartRenderer(BaseRenderer):
    media_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    format = 'multipart'
    charset = 'utf-8'
    BOUNDARY = 'BoUnDaRyStRiNg' if django.VERSION >= (1, 5) else b'BoUnDaRyStRiNg'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return encode_multipart(self.BOUNDARY, data)

