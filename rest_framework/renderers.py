"""
Renderers are used to serialize a response into specific media types.

They give us a generic way of being able to handle various media types
on the response, such as JSON encoded data or HTML output.

REST framework also provides an HTML renderer the renders the browsable API.
"""
from __future__ import unicode_literals

import json

import django
from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Page
from django.http.multipartparser import parse_header
from django.template import Context, RequestContext, Template, loader
from django.test.client import encode_multipart
from django.utils import six

from rest_framework import VERSION, exceptions, serializers, status
from rest_framework.compat import (
    INDENT_SEPARATORS, LONG_SEPARATORS, SHORT_SEPARATORS
)
from rest_framework.exceptions import ParseError
from rest_framework.request import is_form_media_type, override_method
from rest_framework.settings import api_settings
from rest_framework.utils import encoders
from rest_framework.utils.breadcrumbs import get_breadcrumbs
from rest_framework.utils.field_mapping import ClassLookupDict


def zero_as_none(value):
    return None if value == 0 else value


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
        raise NotImplementedError('Renderer class requires .render() to be implemented')


class JSONRenderer(BaseRenderer):
    """
    Renderer which serializes to JSON.
    """

    media_type = 'application/json'
    format = 'json'
    encoder_class = encoders.JSONEncoder
    ensure_ascii = not api_settings.UNICODE_JSON
    compact = api_settings.COMPACT_JSON

    # We don't set a charset because JSON is a binary encoding,
    # that can be encoded as utf-8, utf-16 or utf-32.
    # See: http://www.ietf.org/rfc/rfc4627.txt
    # Also: http://lucumr.pocoo.org/2013/7/19/application-mimetypes-and-encodings/
    charset = None

    def get_indent(self, accepted_media_type, renderer_context):
        if accepted_media_type:
            # If the media type looks like 'application/json; indent=4',
            # then pretty print the result.
            # Note that we coerce `indent=0` into `indent=None`.
            base_media_type, params = parse_header(accepted_media_type.encode('ascii'))
            try:
                return zero_as_none(max(min(int(params['indent']), 8), 0))
            except (KeyError, ValueError, TypeError):
                pass

        # If 'indent' is provided in the context, then pretty print the result.
        # E.g. If we're being called by the BrowsableAPIRenderer.
        return renderer_context.get('indent', None)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render `data` into JSON, returning a bytestring.
        """
        if data is None:
            return bytes()

        renderer_context = renderer_context or {}
        indent = self.get_indent(accepted_media_type, renderer_context)

        if indent is None:
            separators = SHORT_SEPARATORS if self.compact else LONG_SEPARATORS
        else:
            separators = INDENT_SEPARATORS

        ret = json.dumps(
            data, cls=self.encoder_class,
            indent=indent, ensure_ascii=self.ensure_ascii,
            separators=separators
        )

        # On python 2.x json.dumps() returns bytestrings if ensure_ascii=True,
        # but if ensure_ascii=False, the return type is underspecified,
        # and may (or may not) be unicode.
        # On python 3.x json.dumps() returns unicode strings.
        if isinstance(ret, six.text_type):
            # We always fully escape \u2028 and \u2029 to ensure we output JSON
            # that is a strict javascript subset. If bytes were returned
            # by json.dumps() then we don't have these characters in any case.
            # See: http://timelessrepo.com/json-isnt-a-javascript-subset
            ret = ret.replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
            return bytes(ret.encode('utf-8'))
        return ret


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
        raise ImproperlyConfigured(
            'Returned a template response with no `template_name` attribute set on either the view or response'
        )

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
    charset = 'utf-8'
    template_pack = 'rest_framework/horizontal/'
    base_template = 'form.html'

    default_style = ClassLookupDict({
        serializers.Field: {
            'base_template': 'input.html',
            'input_type': 'text'
        },
        serializers.EmailField: {
            'base_template': 'input.html',
            'input_type': 'email'
        },
        serializers.URLField: {
            'base_template': 'input.html',
            'input_type': 'url'
        },
        serializers.IntegerField: {
            'base_template': 'input.html',
            'input_type': 'number'
        },
        serializers.DateTimeField: {
            'base_template': 'input.html',
            'input_type': 'datetime-local'
        },
        serializers.DateField: {
            'base_template': 'input.html',
            'input_type': 'date'
        },
        serializers.TimeField: {
            'base_template': 'input.html',
            'input_type': 'time'
        },
        serializers.FileField: {
            'base_template': 'input.html',
            'input_type': 'file'
        },
        serializers.BooleanField: {
            'base_template': 'checkbox.html'
        },
        serializers.ChoiceField: {
            'base_template': 'select.html',  # Also valid: 'radio.html'
        },
        serializers.MultipleChoiceField: {
            'base_template': 'select_multiple.html',  # Also valid: 'checkbox_multiple.html'
        },
        serializers.RelatedField: {
            'base_template': 'select.html',  # Also valid: 'radio.html'
        },
        serializers.ManyRelatedField: {
            'base_template': 'select_multiple.html',  # Also valid: 'checkbox_multiple.html'
        },
        serializers.Serializer: {
            'base_template': 'fieldset.html'
        },
        serializers.ListSerializer: {
            'base_template': 'list_fieldset.html'
        },
        serializers.FilePathField: {
            'base_template': 'select.html',
        },
    })

    def render_field(self, field, parent_style):
        if isinstance(field._field, serializers.HiddenField):
            return ''

        style = dict(self.default_style[field])
        style.update(field.style)
        if 'template_pack' not in style:
            style['template_pack'] = parent_style.get('template_pack', self.template_pack)
        style['renderer'] = self

        # Get a clone of the field with text-only value representation.
        field = field.as_form_field()

        if style.get('input_type') == 'datetime-local' and isinstance(field.value, six.text_type):
            field.value = field.value.rstrip('Z')

        if 'template' in style:
            template_name = style['template']
        else:
            template_name = style['template_pack'].strip('/') + '/' + style['base_template']

        template = loader.get_template(template_name)
        context = Context({'field': field, 'style': style})
        return template.render(context)

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render serializer data and return an HTML form, as a string.
        """
        form = data.serializer
        meta = getattr(form, 'Meta', None)
        style = getattr(meta, 'style', {})
        if 'template_pack' not in style:
            style['template_pack'] = self.template_pack
        if 'base_template' not in style:
            style['base_template'] = self.base_template
        style['renderer'] = self

        # This API needs to be finessed and finalized for 3.1
        if 'template' in renderer_context:
            template_name = renderer_context['template']
        elif 'template' in style:
            template_name = style['template']
        else:
            template_name = style['template_pack'].strip('/') + '/' + style['base_template']

        renderer_context = renderer_context or {}
        request = renderer_context['request']
        template = loader.get_template(template_name)
        context = RequestContext(request, {
            'form': form,
            'style': style
        })
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
        if method not in view.allowed_methods:
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

    def _get_serializer(self, serializer_class, view_instance, request, *args, **kwargs):
        kwargs['context'] = {
            'request': request,
            'format': self.format,
            'view': view_instance
        }
        return serializer_class(*args, **kwargs)

    def get_rendered_html_form(self, data, view, method, request):
        """
        Return a string representing a rendered HTML form, possibly bound to
        either the input or output data.

        In the absence of the View having an associated form then return None.
        """
        # See issue #2089 for refactoring this.
        serializer = getattr(data, 'serializer', None)
        if serializer and not getattr(serializer, 'many', False):
            instance = getattr(serializer, 'instance', None)
            if isinstance(instance, Page):
                instance = None
        else:
            instance = None

        # If this is valid serializer data, and the form is for the same
        # HTTP method as was used in the request then use the existing
        # serializer instance, rather than dynamically creating a new one.
        if request.method == method and serializer is not None:
            try:
                kwargs = {'data': request.data}
            except ParseError:
                kwargs = {}
            existing_serializer = serializer
        else:
            kwargs = {}
            existing_serializer = None

        with override_method(view, request, method) as request:
            if not self.show_form_for_method(view, method, request, instance):
                return

            if method in ('DELETE', 'OPTIONS'):
                return True  # Don't actually need to return a form

            has_serializer = getattr(view, 'get_serializer', None)
            has_serializer_class = getattr(view, 'serializer_class', None)

            if (
                (not has_serializer and not has_serializer_class) or
                not any(is_form_media_type(parser.media_type) for parser in view.parser_classes)
            ):
                return

            if existing_serializer is not None:
                serializer = existing_serializer
            else:
                if has_serializer:
                    if method in ('PUT', 'PATCH'):
                        serializer = view.get_serializer(instance=instance, **kwargs)
                    else:
                        serializer = view.get_serializer(**kwargs)
                else:
                    # at this point we must have a serializer_class
                    if method in ('PUT', 'PATCH'):
                        serializer = self._get_serializer(view.serializer_class, view,
                                                          request, instance=instance, **kwargs)
                    else:
                        serializer = self._get_serializer(view.serializer_class, view,
                                                          request, **kwargs)

            if hasattr(serializer, 'initial_data'):
                serializer.is_valid()

            form_renderer = self.form_renderer_class()
            return form_renderer.render(
                serializer.data,
                self.accepted_media_type,
                dict(
                    list(self.renderer_context.items()) +
                    [('template', 'rest_framework/api_form.html')]
                )
            )

    def get_raw_data_form(self, data, view, method, request):
        """
        Returns a form that allows for arbitrary content types to be tunneled
        via standard HTML forms.
        (Which are typically application/x-www-form-urlencoded)
        """
        # See issue #2089 for refactoring this.
        serializer = getattr(data, 'serializer', None)
        if serializer and not getattr(serializer, 'many', False):
            instance = getattr(serializer, 'instance', None)
            if isinstance(instance, Page):
                instance = None
        else:
            instance = None

        with override_method(view, request, method) as request:
            # If we're not using content overloading there's no point in
            # supplying a generic form, as the view won't treat the form's
            # value as the content of the request.
            if not (api_settings.FORM_CONTENT_OVERRIDE and
                    api_settings.FORM_CONTENTTYPE_OVERRIDE):
                return None

            # Check permissions
            if not self.show_form_for_method(view, method, request, instance):
                return

            # If possible, serialize the initial content for the generic form
            default_parser = view.parser_classes[0]
            renderer_class = getattr(default_parser, 'renderer_class', None)
            if (hasattr(view, 'get_serializer') and renderer_class):
                # View has a serializer defined and parser class has a
                # corresponding renderer that can be used to render the data.

                if method in ('PUT', 'PATCH'):
                    serializer = view.get_serializer(instance=instance)
                else:
                    serializer = view.get_serializer()

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

    def get_description(self, view, status_code):
        if status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN):
            return ''
        return view.get_view_description(html=True)

    def get_breadcrumbs(self, request):
        return get_breadcrumbs(request.path, request)

    def get_context(self, data, accepted_media_type, renderer_context):
        """
        Returns the context used to render.
        """
        view = renderer_context['view']
        request = renderer_context['request']
        response = renderer_context['response']

        renderer = self.get_default_renderer(view)

        raw_data_post_form = self.get_raw_data_form(data, view, 'POST', request)
        raw_data_put_form = self.get_raw_data_form(data, view, 'PUT', request)
        raw_data_patch_form = self.get_raw_data_form(data, view, 'PATCH', request)
        raw_data_put_or_patch_form = raw_data_put_form or raw_data_patch_form

        response_headers = dict(response.items())
        renderer_content_type = ''
        if renderer:
            renderer_content_type = '%s' % renderer.media_type
            if renderer.charset:
                renderer_content_type += ' ;%s' % renderer.charset
        response_headers['Content-Type'] = renderer_content_type

        if getattr(view, 'paginator', None) and view.paginator.display_page_controls:
            paginator = view.paginator
        else:
            paginator = None

        context = {
            'content': self.get_content(renderer, data, accepted_media_type, renderer_context),
            'view': view,
            'request': request,
            'response': response,
            'description': self.get_description(view, response.status_code),
            'name': self.get_name(view),
            'version': VERSION,
            'paginator': paginator,
            'breadcrumblist': self.get_breadcrumbs(request),
            'allowed_methods': view.allowed_methods,
            'available_formats': [renderer_cls.format for renderer_cls in view.renderer_classes],
            'response_headers': response_headers,

            'put_form': self.get_rendered_html_form(data, view, 'PUT', request),
            'post_form': self.get_rendered_html_form(data, view, 'POST', request),
            'delete_form': self.get_rendered_html_form(data, view, 'DELETE', request),
            'options_form': self.get_rendered_html_form(data, view, 'OPTIONS', request),

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


class AdminRenderer(BrowsableAPIRenderer):
    template = 'rest_framework/admin.html'
    format = 'admin'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        self.accepted_media_type = accepted_media_type or ''
        self.renderer_context = renderer_context or {}

        response = renderer_context['response']
        request = renderer_context['request']
        view = self.renderer_context['view']

        if response.status_code == status.HTTP_400_BAD_REQUEST:
            # Errors still need to display the list or detail information.
            # The only way we can get at that is to simulate a GET request.
            self.error_form = self.get_rendered_html_form(data, view, request.method, request)
            self.error_title = {'POST': 'Create', 'PUT': 'Edit'}.get(request.method, 'Errors')

            with override_method(view, request, 'GET') as request:
                response = view.get(request, *view.args, **view.kwargs)
            data = response.data

        template = loader.get_template(self.template)
        context = self.get_context(data, accepted_media_type, renderer_context)
        context = RequestContext(renderer_context['request'], context)
        ret = template.render(context)

        # Creation and deletion should use redirects in the admin style.
        if (response.status_code == status.HTTP_201_CREATED) and ('Location' in response):
            response.status_code = status.HTTP_302_FOUND
            response['Location'] = request.build_absolute_uri()
            ret = ''

        if response.status_code == status.HTTP_204_NO_CONTENT:
            response.status_code = status.HTTP_302_FOUND
            try:
                # Attempt to get the parent breadcrumb URL.
                response['Location'] = self.get_breadcrumbs(request)[-2][1]
            except KeyError:
                # Otherwise reload current URL to get a 'Not Found' page.
                response['Location'] = request.full_path
            ret = ''

        return ret

    def get_context(self, data, accepted_media_type, renderer_context):
        """
        Render the HTML for the browsable API representation.
        """
        context = super(AdminRenderer, self).get_context(
            data, accepted_media_type, renderer_context
        )

        paginator = getattr(context['view'], 'paginator', None)
        if (paginator is not None and data is not None):
            try:
                results = paginator.get_results(data)
            except KeyError:
                results = data
        else:
            results = data

        if results is None:
            header = {}
            style = 'detail'
        elif isinstance(results, list):
            header = results[0] if results else {}
            style = 'list'
        else:
            header = results
            style = 'detail'

        columns = [key for key in header.keys() if key != 'url']
        details = [key for key in header.keys() if key != 'url']

        context['style'] = style
        context['columns'] = columns
        context['details'] = details
        context['results'] = results
        context['error_form'] = getattr(self, 'error_form', None)
        context['error_title'] = getattr(self, 'error_title', None)
        return context


class MultiPartRenderer(BaseRenderer):
    media_type = 'multipart/form-data; boundary=BoUnDaRyStRiNg'
    format = 'multipart'
    charset = 'utf-8'
    BOUNDARY = 'BoUnDaRyStRiNg' if django.VERSION >= (1, 5) else b'BoUnDaRyStRiNg'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if hasattr(data, 'items'):
            for key, value in data.items():
                assert not isinstance(value, dict), (
                    "Test data contained a dictionary value for key '%s', "
                    "but multipart uploads do not support nested data. "
                    "You may want to consider using format='JSON' in this "
                    "test case." % key
                )
        return encode_multipart(self.BOUNDARY, data)
