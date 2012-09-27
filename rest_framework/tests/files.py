# from django.test import TestCase
# from django import forms

# from django.test.client import RequestFactory
# from rest_framework.views import View
# from rest_framework.response import Response

# import StringIO


# class UploadFilesTests(TestCase):
#     """Check uploading of files"""
#     def setUp(self):
#         self.factory = RequestFactory()

#     def test_upload_file(self):

#         class FileForm(forms.Form):
#             file = forms.FileField()

#         class MockView(View):
#             permissions = ()
#             form = FileForm

#             def post(self, request, *args, **kwargs):
#                 return Response({'FILE_NAME': self.CONTENT['file'].name,
#                         'FILE_CONTENT': self.CONTENT['file'].read()})

#         file = StringIO.StringIO('stuff')
#         file.name = 'stuff.txt'
#         request = self.factory.post('/', {'file': file})
#         view = MockView.as_view()
#         response = view(request)
#         self.assertEquals(response.raw_content, {"FILE_CONTENT": "stuff", "FILE_NAME": "stuff.txt"})
