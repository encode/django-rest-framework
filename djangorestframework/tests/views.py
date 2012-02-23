from django.conf.urls.defaults import patterns, url
from django.http import HttpResponse
from django.test import TestCase
from django.test import Client
from django import forms
from django.db import models

from djangorestframework.views import View
from djangorestframework.parsers import JSONParser
from djangorestframework.resources import ModelResource
from djangorestframework.views import ListOrCreateModelView, InstanceModelView

from StringIO import StringIO


class MockView(View):
    """This is a basic mock view"""
    pass


class MockViewFinal(View):
    """View with final() override"""

    def final(self, request, response, *args, **kwargs):
        return HttpResponse('{"test": "passed"}', content_type="application/json")

class ResourceMockView(View):
    """This is a resource-based mock view"""

    class MockForm(forms.Form):
        foo = forms.BooleanField(required=False)
        bar = forms.IntegerField(help_text='Must be an integer.')
        baz = forms.CharField(max_length=32)

    form = MockForm

class MockResource(ModelResource):
    """This is a mock model-based resource"""

    class MockResourceModel(models.Model):
        foo = models.BooleanField()
        bar = models.IntegerField(help_text='Must be an integer.')
        baz = models.CharField(max_length=32, help_text='Free text.  Max length 32 chars.')

    model = MockResourceModel
    fields = ('foo', 'bar', 'baz')

urlpatterns = patterns('djangorestframework.utils.staticviews',
    url(r'^accounts/login$', 'api_login'),
    url(r'^accounts/logout$', 'api_logout'),
    url(r'^mock/$', MockView.as_view()),
    url(r'^mock/final/$', MockViewFinal.as_view()),
    url(r'^resourcemock/$', ResourceMockView.as_view()),
    url(r'^model/$', ListOrCreateModelView.as_view(resource=MockResource)),
    url(r'^model/(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=MockResource)),
)

class BaseViewTests(TestCase):
    """Test the base view class of djangorestframework"""
    urls = 'djangorestframework.tests.views'

    def test_view_call_final(self):
        response = self.client.options('/mock/final/')
        self.assertEqual(response['Content-Type'].split(';')[0], "application/json")
        parser = JSONParser(None)
        (data, files) = parser.parse(StringIO(response.content))
        self.assertEqual(data['test'], 'passed')

    def test_options_method_simple_view(self):
        response = self.client.options('/mock/')
        self._verify_options_response(response,
                                      name='Mock',
                                      description='This is a basic mock view')

    def test_options_method_resource_view(self):
        response = self.client.options('/resourcemock/')
        self._verify_options_response(response,
                                      name='Resource Mock',
                                      description='This is a resource-based mock view',
                                      fields={'foo':'BooleanField',
                                              'bar':'IntegerField',
                                              'baz':'CharField',
                                              })

    def test_options_method_model_resource_list_view(self):
        response = self.client.options('/model/')
        self._verify_options_response(response,
                                      name='Mock List',
                                      description='This is a mock model-based resource',
                                      fields={'foo':'BooleanField',
                                              'bar':'IntegerField',
                                              'baz':'CharField',
                                              })

    def test_options_method_model_resource_detail_view(self):
        response = self.client.options('/model/0/')
        self._verify_options_response(response,
                                      name='Mock Instance',
                                      description='This is a mock model-based resource',
                                      fields={'foo':'BooleanField',
                                              'bar':'IntegerField',
                                              'baz':'CharField',
                                              })

    def _verify_options_response(self, response, name, description, fields=None, status=200,
                                 mime_type='application/json'):
        self.assertEqual(response.status_code, status)
        self.assertEqual(response['Content-Type'].split(';')[0], mime_type)
        parser = JSONParser(None)
        (data, files) = parser.parse(StringIO(response.content))
        self.assertTrue('application/json' in data['renders'])
        self.assertEqual(name, data['name'])
        self.assertEqual(description, data['description'])
        if fields is None:
            self.assertFalse(hasattr(data, 'fields'))
        else:
            self.assertEqual(data['fields'], fields)


class ExtraViewsTests(TestCase):
    """Test the extra views djangorestframework provides"""
    urls = 'djangorestframework.tests.views'

    def test_login_view(self):
        """Ensure the login view exists"""
        response = self.client.get('/accounts/login')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'].split(';')[0], 'text/html')

    def test_logout_view(self):
        """Ensure the logout view exists"""
        response = self.client.get('/accounts/logout')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'].split(';')[0], 'text/html')

    # TODO: Add login/logout behaviour tests

