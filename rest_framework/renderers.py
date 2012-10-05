"""
Renderers are used to serialize a View's output into specific media types.

Django REST framework also provides HTML and PlainText renderers that help self-document the API,
by serializing the output along with documentation regarding the View, output status and headers,
and providing forms and links depending on the allowed methods, renderers and parsers on the View.
"""
import string
from django import forms
from django.template import RequestContext, loader
from django.utils import simplejson as json
from rest_framework.compat import yaml
from rest_framework.settings import api_settings
from rest_framework.request import clone_request
from rest_framework.utils import dict2xml
from rest_framework.utils import encoders
from rest_framework.utils.breadcrumbs import get_breadcrumbs
from rest_framework.utils.mediatypes import get_media_type_params, add_media_type_param
from rest_framework import VERSION
from rest_framework import serializers


class BaseRenderer(object):
    """
    All renderers must extend this class, set the :attr:`media_type` attribute,
    and override the :meth:`render` method.
    """

    media_type = None
    format = None

    def __init__(self, view=None):
        self.view = view

    def render(self, data=None, accepted_media_type=None):
        raise NotImplemented('Renderer class requires .render() to be implemented')


class JSONRenderer(BaseRenderer):
    """
    Renderer which serializes to json.
    """

    media_type = 'application/json'
    format = 'json'
    encoder_class = encoders.JSONEncoder

    def render(self, data=None, accepted_media_type=None):
        """
        Render `obj` into json.
        """
        if data is None:
            return ''

        # If the media type looks like 'application/json; indent=4', then
        # pretty print the result.
        indent = get_media_type_params(accepted_media_type).get('indent', None)
        sort_keys = False
        try:
            indent = max(min(int(indent), 8), 0)
            sort_keys = True
        except (ValueError, TypeError):
            indent = None

        return json.dumps(data, cls=self.encoder_class,
                          indent=indent, sort_keys=sort_keys)


class JSONPRenderer(JSONRenderer):
    """
    Renderer which serializes to json,
    wrapping the json output in a callback function.
    """

    media_type = 'application/javascript'
    format = 'jsonp'
    callback_parameter = 'callback'
    default_callback = 'callback'

    def get_callback(self):
        """
        Determine the name of the callback to wrap around the json output.
        """
        params = self.view.request.GET
        return params.get(self.callback_parameter, self.default_callback)

    def render(self, data=None, accepted_media_type=None):
        """
        Renders into jsonp, wrapping the json output in a callback function.

        Clients may set the callback function name using a query parameter
        on the URL, for example: ?callback=exampleCallbackName
        """
        callback = self.get_callback()
        json = super(JSONPRenderer, self).render(data, accepted_media_type)
        return "%s(%s);" % (callback, json)


class XMLRenderer(BaseRenderer):
    """
    Renderer which serializes to XML.
    """

    media_type = 'application/xml'
    format = 'xml'

    def render(self, data=None, accepted_media_type=None):
        """
        Renders *obj* into serialized XML.
        """
        if data is None:
            return ''
        return dict2xml(data)


class YAMLRenderer(BaseRenderer):
    """
    Renderer which serializes to YAML.
    """

    media_type = 'application/yaml'
    format = 'yaml'

    def render(self, data=None, accepted_media_type=None):
        """
        Renders *obj* into serialized YAML.
        """
        if data is None:
            return ''

        return yaml.safe_dump(data)


class HTMLTemplateRenderer(BaseRenderer):
    """
    A Base class provided for convenience.

    Render the object simply by using the given template.
    To create a template renderer, subclass this class, and set
    the :attr:`media_type` and :attr:`template` attributes.
    """

    media_type = 'text/html'
    format = 'html'
    template = None

    def render(self, data=None, accepted_media_type=None):
        """
        Renders *obj* using the :attr:`template` specified on the class.
        """
        if data is None:
            return ''

        template = loader.get_template(self.template)
        context = RequestContext(self.view.request, {'object': data})
        return template.render(context)


class DocumentingHTMLRenderer(BaseRenderer):
    """
    HTML renderer used to self-document the API.
    """
    media_type = 'text/html'
    format = 'api'
    template = 'rest_framework/api.html'

    def get_content(self, view, request, data, accepted_media_type):
        """
        Get the content as if it had been rendered by a non-documenting renderer.

        (Typically this will be the content as it would have been if the Resource had been
        requested with an 'Accept: */*' header, although with verbose style formatting if appropriate.)
        """

        # Find the first valid renderer and render the content. (Don't use another documenting renderer.)
        renderers = [renderer for renderer in view.renderer_classes
                     if not issubclass(renderer, DocumentingHTMLRenderer)]
        if not renderers:
            return '[No renderers were found]'

        accepted_media_type = add_media_type_param(accepted_media_type, 'indent', '4')
        content = renderers[0](view).render(data, accepted_media_type)
        if not all(char in string.printable for char in content):
            return '[%d bytes of binary content]'

        return content

    def get_form(self, view, method, request):
        """
        Get a form, possibly bound to either the input or output data.
        In the absence on of the Resource having an associated form then
        provide a form that can be used to submit arbitrary content.
        """
        if not method in view.allowed_methods:
            return  # Not a valid method

        if not api_settings.FORM_METHOD_OVERRIDE:
            return  # Cannot use form overloading

        request = clone_request(request, method)
        if not view.has_permission(request):
            return  # Don't have permission

        if method == 'DELETE' or method == 'OPTIONS':
            return True  # Don't actually need to return a form

        if not getattr(view, 'get_serializer', None):
            return self.get_generic_content_form(view)

        #  We need to map our Fields to Django's Fields.
        # TODO: Remove this and just render serializer fields directly
        field_mapping = {
            serializers.FloatField: forms.FloatField,
            serializers.IntegerField: forms.IntegerField,
            serializers.DateTimeField: forms.DateTimeField,
            serializers.DateField: forms.DateField,
            serializers.EmailField: forms.EmailField,
            serializers.CharField: forms.CharField,
            serializers.BooleanField: forms.BooleanField,
            serializers.PrimaryKeyRelatedField: forms.ModelChoiceField,
            serializers.ManyPrimaryKeyRelatedField: forms.ModelMultipleChoiceField
        }

        # Creating an on the fly form see: http://stackoverflow.com/questions/3915024/dynamically-creating-classes-python
        fields = {}
        obj, data = None, None
        if getattr(view, 'object', None):
            obj = view.object

        serializer = view.get_serializer(instance=obj)
        for k, v in serializer.get_fields(True).items():
            print k, v
            if getattr(v, 'readonly', True):
                continue

            kwargs = {}
            if getattr(v, 'queryset', None):
                kwargs['queryset'] = getattr(v, 'queryset', None)

            try:
                fields[k] = field_mapping[v.__class__](**kwargs)
            except KeyError:
                fields[k] = forms.CharField()

        OnTheFlyForm = type("OnTheFlyForm", (forms.Form,), fields)
        if obj and not view.request.method == 'DELETE':  # Don't fill in the form when the object is deleted
            data = serializer.data
        form_instance = OnTheFlyForm(data)
        return form_instance

    def get_generic_content_form(self, view):
        """
        Returns a form that allows for arbitrary content types to be tunneled via standard HTML forms
        (Which are typically application/x-www-form-urlencoded)
        """

        # If we're not using content overloading there's no point in supplying a generic form,
        # as the view won't treat the form's value as the content of the request.
        if not (api_settings.FORM_CONTENT_OVERRIDE
                and api_settings.FORM_CONTENTTYPE_OVERRIDE):
            return None

        # NB. http://jacobian.org/writing/dynamic-form-generation/
        class GenericContentForm(forms.Form):
            def __init__(self, view, request):
                """We don't know the names of the fields we want to set until the point the form is instantiated,
                as they are determined by the Resource the form is being created against.
                Add the fields dynamically."""
                super(GenericContentForm, self).__init__()

                parsed_media_types = [parser.media_type for parser in view.parser_classes]
                contenttype_choices = [(media_type, media_type) for media_type in parsed_media_types]
                initial_contenttype = parsed_media_types[0]

                self.fields[api_settings.FORM_CONTENTTYPE_OVERRIDE] = forms.ChoiceField(
                    label='Content Type',
                    choices=contenttype_choices,
                    initial=initial_contenttype
                )
                self.fields[api_settings.FORM_CONTENT_OVERRIDE] = forms.CharField(
                    label='Content',
                    widget=forms.Textarea
                )

        # If either of these reserved parameters are turned off then content tunneling is not possible
        if self.view.request._CONTENTTYPE_PARAM is None or self.view.request._CONTENT_PARAM is None:
            return None

        # Okey doke, let's do it
        return GenericContentForm(view, view.request)

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

    def render(self, data=None, accepted_media_type=None):
        """
        Renders *obj* using the :attr:`template` set on the class.

        The context used in the template contains all the information
        needed to self-document the response to this request.
        """
        view = self.view
        request = view.request
        response = view.response

        content = self.get_content(view, request, data, accepted_media_type)

        put_form = self.get_form(view, 'PUT', request)
        post_form = self.get_form(view, 'POST', request)
        delete_form = self.get_form(view, 'DELETE', request)
        options_form = self.get_form(view, 'OPTIONS', request)

        name = self.get_name()
        description = self.get_description()

        breadcrumb_list = get_breadcrumbs(self.view.request.path)

        template = loader.get_template(self.template)
        context = RequestContext(self.view.request, {
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
            'delete_form': delete_form,
            'options_form': options_form,
            'api_settings': api_settings
        })

        ret = template.render(context)

        # Munge DELETE Response code to allow us to return content
        # (Do this *after* we've rendered the template so that we include
        # the normal deletion response code in the output)
        if self.view.response.status_code == 204:
            self.view.response.status_code = 200

        return ret
