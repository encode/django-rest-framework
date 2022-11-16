import django.template.loader
import pytest
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.http import Http404
from django.template import TemplateDoesNotExist, engines
from django.test import TestCase, override_settings
from django.urls import path

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
    path('', example),
    path('permission_denied', permission_denied),
    path('not_found', not_found),
]


@override_settings(ROOT_URLCONF='tests.test_htmlrenderer')
class TemplateHTMLRendererTests(TestCase):
    def setUp(self):
        class MockResponse:
            template_name = None
        self.mock_response = MockResponse()
        self._monkey_patch_get_template()

    def _monkey_patch_get_template(self):
        """
        Monkeypatch get_template
        """
        self.get_template = django.template.loader.get_template

        def get_template(template_name, dirs=None):
            if template_name == 'example.html':
                return engines['django'].from_string("example: {{ object }}")
            raise TemplateDoesNotExist(template_name)

        def select_template(template_name_list, dirs=None, using=None):
            if template_name_list == ['example.html']:
                return engines['django'].from_string("example: {{ object }}")
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
        self.assertEqual(response.content, b"404 Not Found")
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_permission_denied_html_view(self):
        response = self.client.get('/permission_denied')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.content, b"403 Forbidden")
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    # 2 tests below are based on order of if statements in corresponding method
    # of TemplateHTMLRenderer
    def test_get_template_names_returns_own_template_name(self):
        renderer = TemplateHTMLRenderer()
        renderer.template_name = 'test_template'
        template_name = renderer.get_template_names(self.mock_response, view={})
        assert template_name == ['test_template']

    def test_get_template_names_returns_view_template_name(self):
        renderer = TemplateHTMLRenderer()

        class MockResponse:
            template_name = None

        class MockView:
            def get_template_names(self):
                return ['template from get_template_names method']

        class MockView2:
            template_name = 'template from template_name attribute'

        template_name = renderer.get_template_names(self.mock_response,
                                                    MockView())
        assert template_name == ['template from get_template_names method']

        template_name = renderer.get_template_names(self.mock_response,
                                                    MockView2())
        assert template_name == ['template from template_name attribute']

    def test_get_template_names_raises_error_if_no_template_found(self):
        renderer = TemplateHTMLRenderer()
        with pytest.raises(ImproperlyConfigured):
            renderer.get_template_names(self.mock_response, view=object())


@override_settings(ROOT_URLCONF='tests.test_htmlrenderer')
class TemplateHTMLRendererExceptionTests(TestCase):
    def setUp(self):
        """
        Monkeypatch get_template
        """
        self.get_template = django.template.loader.get_template

        def get_template(template_name):
            if template_name == '404.html':
                return engines['django'].from_string("404: {{ detail }}")
            if template_name == '403.html':
                return engines['django'].from_string("403: {{ detail }}")
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
            b"404: Not found", b"404 Not Found"))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

    def test_permission_denied_html_view_with_template(self):
        response = self.client.get('/permission_denied')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(response.content in (b"403: Permission denied", b"403 Forbidden"))
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
