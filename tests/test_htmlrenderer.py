from __future__ import unicode_literals

import django.template.loader
from django.conf.urls import url
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.template import Template, TemplateDoesNotExist
from django.test import TestCase, override_settings
from django.utils import six

from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer,))
def example(request):
    """
    A view that can returns an HTML representation.
    """
    data = {'object': 'foobar'}
    return Response(data, template_name='example.html')


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer,))
def permission_denied(request):
    raise PermissionDenied()


@api_view(('GET',))
@renderer_classes((TemplateHTMLRenderer,))
def not_found(request):
    raise Http404()


urlpatterns = [
    url(r'^$', example),
    url(r'^permission_denied$', permission_denied),
    url(r'^not_found$', not_found),
]


@override_settings(ROOT_URLCONF='tests.test_htmlrenderer')
class TemplateHTMLRendererTests(TestCase):
    def setUp(self):
        """
        Monkeypatch get_template
        """
        self.get_template = django.template.loader.get_template

        def get_template(template_name, dirs=None):
            if template_name == 'example.html':
                return Template("example: {{ object }}")
            raise TemplateDoesNotExist(template_name)

        def select_template(template_name_list, dirs=None, using=None):
            if template_name_list == ['example.html']:
                return Template("example: {{ object }}")
            raise TemplateDoesNotExist(template_name_list[0])

        django.template.loader.get_template = get_template
        django.template.loader.select_template = select_template

    def tearDown(self):
        """
        Revert monkeypatching
        """
        django.template.loader.get_template = self.get_template

    def test_simple_html_view(self):
        response = self.client.get('/')
        self.assertContains(response, "example: foobar")
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_not_found_html_view(self):
        response = self.client.get('/not_found')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.content, six.b("404 Not Found"))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_permission_denied_html_view(self):
        response = self.client.get('/permission_denied')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.content, six.b("403 Forbidden"))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')


@override_settings(ROOT_URLCONF='tests.test_htmlrenderer')
class TemplateHTMLRendererExceptionTests(TestCase):
    def setUp(self):
        """
        Monkeypatch get_template
        """
        self.get_template = django.template.loader.get_template

        def get_template(template_name):
            if template_name == '404.html':
                return Template("404: {{ detail }}")
            if template_name == '403.html':
                return Template("403: {{ detail }}")
            raise TemplateDoesNotExist(template_name)

        django.template.loader.get_template = get_template

    def tearDown(self):
        """
        Revert monkeypatching
        """
        django.template.loader.get_template = self.get_template

    def test_not_found_html_view_with_template(self):
        response = self.client.get('/not_found')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(response.content in (
            six.b("404: Not found"), six.b("404 Not Found")))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_permission_denied_html_view_with_template(self):
        response = self.client.get('/permission_denied')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.content in (
            six.b("403: Permission denied"), six.b("403 Forbidden")))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
