from django.conf.urls.defaults import patterns, url
from django.test import TestCase
from django.template import TemplateDoesNotExist, Template
import django.template.loader
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import HTMLRenderer
from rest_framework.response import Response


@api_view(('GET',))
@renderer_classes((HTMLRenderer,))
def example(request):
    """
    A view that can returns an HTML representation.
    """
    data = {'object': 'foobar'}
    return Response(data, template_name='example.html')


urlpatterns = patterns('',
    url(r'^$', example),
)


class HTMLRendererTests(TestCase):
    urls = 'rest_framework.tests.htmlrenderer'

    def setUp(self):
        """
        Monkeypatch get_template
        """
        self.get_template = django.template.loader.get_template

        def get_template(template_name):
            if template_name == 'example.html':
                return Template("example: {{ object }}")
            raise TemplateDoesNotExist(template_name)

        django.template.loader.get_template = get_template

    def tearDown(self):
        """
        Revert monkeypatching
        """
        django.template.loader.get_template = self.get_template

    def test_simple_html_view(self):
        response = self.client.get('/')
        self.assertContains(response, "example: foobar")
        self.assertEquals(response['Content-Type'], 'text/html')
