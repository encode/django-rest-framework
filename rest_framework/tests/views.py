# from django.core.urlresolvers import reverse
# from django.conf.urls.defaults import patterns, url, include
# from django.http import HttpResponse
# from django.test import TestCase
# from django.utils import simplejson as json

# from rest_framework.views import View


# class MockView(View):
#     """This is a basic mock view"""
#     pass


# class MockViewFinal(View):
#     """View with final() override"""

#     def final(self, request, response, *args, **kwargs):
#         return HttpResponse('{"test": "passed"}', content_type="application/json")


# # class ResourceMockView(View):
# #     """This is a resource-based mock view"""

# #     class MockForm(forms.Form):
# #         foo = forms.BooleanField(required=False)
# #         bar = forms.IntegerField(help_text='Must be an integer.')
# #         baz = forms.CharField(max_length=32)

# #     form = MockForm


# # class MockResource(ModelResource):
# #     """This is a mock model-based resource"""

# #     class MockResourceModel(models.Model):
# #         foo = models.BooleanField()
# #         bar = models.IntegerField(help_text='Must be an integer.')
# #         baz = models.CharField(max_length=32, help_text='Free text.  Max length 32 chars.')

# #     model = MockResourceModel
# #     fields = ('foo', 'bar', 'baz')

# urlpatterns = patterns('',
#     url(r'^mock/$', MockView.as_view()),
#     url(r'^mock/final/$', MockViewFinal.as_view()),
#     # url(r'^resourcemock/$', ResourceMockView.as_view()),
#     # url(r'^model/$', ListOrCreateModelView.as_view(resource=MockResource)),
#     # url(r'^model/(?P<pk>[^/]+)/$', InstanceModelView.as_view(resource=MockResource)),
#     url(r'^restframework/', include('rest_framework.urls', namespace='rest_framework')),
# )


# class BaseViewTests(TestCase):
#     """Test the base view class of rest_framework"""
#     urls = 'rest_framework.tests.views'

#     def test_view_call_final(self):
#         response = self.client.options('/mock/final/')
#         self.assertEqual(response['Content-Type'].split(';')[0], "application/json")
#         data = json.loads(response.content)
#         self.assertEqual(data['test'], 'passed')

#     def test_options_method_simple_view(self):
#         response = self.client.options('/mock/')
#         self._verify_options_response(response,
#                                       name='Mock',
#                                       description='This is a basic mock view')

#     def test_options_method_resource_view(self):
#         response = self.client.options('/resourcemock/')
#         self._verify_options_response(response,
#                                       name='Resource Mock',
#                                       description='This is a resource-based mock view',
#                                       fields={'foo': 'BooleanField',
#                                               'bar': 'IntegerField',
#                                               'baz': 'CharField',
#                                               })

#     def test_options_method_model_resource_list_view(self):
#         response = self.client.options('/model/')
#         self._verify_options_response(response,
#                                       name='Mock List',
#                                       description='This is a mock model-based resource',
#                                       fields={'foo': 'BooleanField',
#                                               'bar': 'IntegerField',
#                                               'baz': 'CharField',
#                                               })

#     def test_options_method_model_resource_detail_view(self):
#         response = self.client.options('/model/0/')
#         self._verify_options_response(response,
#                                       name='Mock Instance',
#                                       description='This is a mock model-based resource',
#                                       fields={'foo': 'BooleanField',
#                                               'bar': 'IntegerField',
#                                               'baz': 'CharField',
#                                               })

#     def _verify_options_response(self, response, name, description, fields=None, status=200,
#                                  mime_type='application/json'):
#         self.assertEqual(response.status_code, status)
#         self.assertEqual(response['Content-Type'].split(';')[0], mime_type)
#         data = json.loads(response.content)
#         self.assertTrue('application/json' in data['renders'])
#         self.assertEqual(name, data['name'])
#         self.assertEqual(description, data['description'])
#         if fields is None:
#             self.assertFalse(hasattr(data, 'fields'))
#         else:
#             self.assertEqual(data['fields'], fields)


# class ExtraViewsTests(TestCase):
#     """Test the extra views rest_framework provides"""
#     urls = 'rest_framework.tests.views'

#     def test_login_view(self):
#         """Ensure the login view exists"""
#         response = self.client.get(reverse('rest_framework:login'))
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response['Content-Type'].split(';')[0], 'text/html')

#     def test_logout_view(self):
#         """Ensure the logout view exists"""
#         response = self.client.get(reverse('rest_framework:logout'))
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response['Content-Type'].split(';')[0], 'text/html')
