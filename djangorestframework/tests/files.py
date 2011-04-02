from django.test import TestCase
from django import forms
from djangorestframework.compat import RequestFactory
from djangorestframework.resource import Resource
import StringIO

class UploadFilesTests(TestCase):
    """Check uploading of files"""
    def setUp(self):
        self.factory = RequestFactory()

    def test_upload_file(self):


        class FileForm(forms.Form):
            file = forms.FileField

        class MockResource(Resource):
            allowed_methods = anon_allowed_methods = ('POST',)
            form = FileForm

            def post(self, request, auth, content, *args, **kwargs):
                #self.uploaded = content.file
                return {'FILE_NAME': content['file'].name,
                        'FILE_CONTENT': content['file'].read()}
                
        file = StringIO.StringIO('stuff')
        file.name = 'stuff.txt'
        request = self.factory.post('/', {'file': file})
        view = MockResource.as_view()
        response = view(request)
        self.assertEquals(response.content, '{"FILE_CONTENT": "stuff", "FILE_NAME": "stuff.txt"}')





