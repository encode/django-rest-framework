"""
Renderers are used to serialize a response into specific media types.

They give us a generic way of being able to handle various media types
on the response, such as JSON encoded data or HTML output.

REST framework also provides an HTML renderer the renders the browsable API.
"""
from __future__ import unicode_literals

import copy
import json
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
from rest_framework.settings import api_settings
from rest_framework.request import clone_request
from rest_framework.utils import encoders
from rest_framework.utils.breadcrumbs import get_breadcrumbs
from rest_framework.utils.formatting import get_view_name, get_view_description
from rest_framework import exceptions, parsers, status, VERSION


class BaseRenderer(object):
    """
    All renderers should extend this class, setting the `media_type`
    and `format` attributes, and override the `.render()` method.
    """

    media_type = None
    format = None
    charset = 'utf-8'

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
    charset = 'utf-8'
    # Note that JSON encodings must be utf-8, utf-16 or utf-32.
    # See: http://www.ietf.org/rfc/rfc4627.txt

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON.
        """
        if data is None:
            return ''

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
            return bytes(ret.encode(self.charset))
        return ret


class UnicodeJSONRenderer(JSONRenderer):
    ensure_ascii = False
    charset = 'utf-8'
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
        Renders *obj* into serialized XML.
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

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Renders *obj* into serialized YAML.
        """
        assert yaml, 'YAMLRenderer requires pyyaml to be installed'

        if data is None:
            return ''

        return yaml.dump(data, stream=None, encoding=self.charset, Dumper=self.encoder)


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
        raise ImproperlyConfigured('Returned a template response with no template_name')

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


class BrowsableAPIRenderer(BaseRenderer):
    """
    HTML renderer used to self-document the API.
    """
    media_type = 'text/html'
    format = 'api'
    template = 'rest_framework/api.html'
    charset = 'utf-8'

    def get_default_renderer(self, view):
        """
        Return an instance of the first valid renderer.
        (Don't use another documenting renderer.)
        """
        renderers = [renderer for renderer in view.renderer_classes
                     if not issubclass(renderer, BrowsableAPIRenderer)]
        if not renderers:
            return None
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

        if renderer.charset is None:
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

    def serializer_to_form_fields(self, serializer):
        fields = {}
        for k, v in serializer.get_fields().items():
            if getattr(v, 'read_only', True):
                continue

            kwargs = {}
            kwargs['required'] = v.required

            #if getattr(v, 'queryset', None):
            #    kwargs['queryset'] = v.queryset

            if getattr(v, 'choices', None) is not None:
                kwargs['choices'] = v.choices

            if getattr(v, 'regex', None) is not None:
                kwargs['regex'] = v.regex

            if getattr(v, 'widget', None):
                widget = copy.deepcopy(v.widget)
                kwargs['widget'] = widget

            if getattr(v, 'default', None) is not None:
                kwargs['initial'] = v.default

            if getattr(v, 'label', None) is not None:
                kwargs['label'] = v.label

            if getattr(v, 'help_text', None) is not None:
                kwargs['help_text'] = v.help_text

            fields[k] = v.form_field_class(**kwargs)

        return fields

    def _get_form(self, view, method, request):
        # We need to impersonate a request with the correct method,
        # so that eg. any dynamic get_serializer_class methods return the
        # correct form for each method.
        restore = view.request
        request = clone_request(request, method)
        view.request = request
        try:
            return self.get_form(view, method, request)
        finally:
            view.request = restore

    def _get_raw_data_form(self, view, method, request, media_types):
        # We need to impersonate a request with the correct method,
        # so that eg. any dynamic get_serializer_class methods return the
        # correct form for each method.
        restore = view.request
        request = clone_request(request, method)
        view.request = request
        try:
            return self.get_raw_data_form(view, method, request, media_types)
        finally:
            view.request = restore

    def get_form(self, view, method, request):
        """
        Get a form, possibly bound to either the input or output data.
        In the absence on of the Resource having an associated form then
        provide a form that can be used to submit arbitrary content.
        """
        obj = getattr(view, 'object', None)
        if not self.show_form_for_method(view, method, request, obj):
            return

        if method in ('DELETE', 'OPTIONS'):
            return True  # Don't actually need to return a form

        if not getattr(view, 'get_serializer', None) or not parsers.FormParser in view.parser_classes:
            return

        serializer = view.get_serializer(instance=obj)
        fields = self.serializer_to_form_fields(serializer)

        # Creating an on the fly form see:
        # http://stackoverflow.com/questions/3915024/dynamically-creating-classes-python
        OnTheFlyForm = type(str("OnTheFlyForm"), (forms.Form,), fields)
        data = (obj is not None) and serializer.data or None
        form_instance = OnTheFlyForm(data)
        return form_instance

    def get_raw_data_form(self, view, method, request, media_types):
        """
        Returns a form that allows for arbitrary content types to be tunneled
        via standard HTML forms.
        (Which are typically application/x-www-form-urlencoded)
        """

        # If we're not using content overloading there's no point in supplying a generic form,
        # as the view won't treat the form's value as the content of the request.
        if not (api_settings.FORM_CONTENT_OVERRIDE
                and api_settings.FORM_CONTENTTYPE_OVERRIDE):
            return None

        # Check permissions
        obj = getattr(view, 'object', None)
        if not self.show_form_for_method(view, method, request, obj):
            return

        content_type_field = api_settings.FORM_CONTENTTYPE_OVERRIDE
        content_field = api_settings.FORM_CONTENT_OVERRIDE
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
                    widget=forms.Textarea
                )

        return GenericContentForm()

    def get_name(self, view):
        return get_view_name(view.__class__, getattr(view, 'suffix', None))

    def get_description(self, view):
        return get_view_description(view.__class__, html=True)

    def get_breadcrumbs(self, request):
        return get_breadcrumbs(request.path)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the HTML for the browsable API representation.
        """
        accepted_media_type = accepted_media_type or ''
        renderer_context = renderer_context or {}

        view = renderer_context['view']
        request = renderer_context['request']
        response = renderer_context['response']
        media_types = [parser.media_type for parser in view.parser_classes]

        renderer = self.get_default_renderer(view)
        content = self.get_content(renderer, data, accepted_media_type, renderer_context)

        put_form = self._get_form(view, 'PUT', request)
        post_form = self._get_form(view, 'POST', request)
        patch_form = self._get_form(view, 'PATCH', request)
        delete_form = self._get_form(view, 'DELETE', request)
        options_form = self._get_form(view, 'OPTIONS', request)

        raw_data_put_form = self._get_raw_data_form(view, 'PUT', request, media_types)
        raw_data_post_form = self._get_raw_data_form(view, 'POST', request, media_types)
        raw_data_patch_form = self._get_raw_data_form(view, 'PATCH', request, media_types)
        raw_data_put_or_patch_form = raw_data_put_form or raw_data_patch_form

        name = self.get_name(view)
        description = self.get_description(view)
        breadcrumb_list = self.get_breadcrumbs(request)

        template = loader.get_template(self.template)
        context = RequestContext(request, {
            'content': content,
            'view': view,
            'request': request,
            'response': response,
            'description': description,
            'name': name,
            'version': VERSION,
            'breadcrumblist': breadcrumb_list,
            'allowed_methods': view.allowed_methods,
            'available_formats': [renderer.format for renderer in view.renderer_classes],

            'put_form': put_form,
            'post_form': post_form,
            'patch_form': patch_form,
            'delete_form': delete_form,
            'options_form': options_form,

            'raw_data_put_form': raw_data_put_form,
            'raw_data_post_form': raw_data_post_form,
            'raw_data_patch_form': raw_data_patch_form,
            'raw_data_put_or_patch_form': raw_data_put_or_patch_form,

            'api_settings': api_settings
        })

        ret = template.render(context)

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include
        # the normal deletion response code in the output)
        if response.status_code == status.HTTP_204_NO_CONTENT:
            response.status_code = status.HTTP_200_OK

        return ret


class MultiPartRenderer(BaseRenderer):
    media_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    format = 'multipart'
    charset = 'utf-8'
    BOUNDARY = 'BoUnDaRyStRiNg'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return encode_multipart(self.BOUNDARY, data)
