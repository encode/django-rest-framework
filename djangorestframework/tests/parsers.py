# """
# ..
#     >>> from djangorestframework.parsers import FormParser
#     >>> from djangorestframework.compat import RequestFactory
#     >>> from djangorestframework.views import View
#     >>> from StringIO import StringIO
#     >>> from urllib import urlencode
#     >>> req = RequestFactory().get('/')
#     >>> some_view = View()
#     >>> some_view.request = req  # Make as if this request had been dispatched
# 
# FormParser
# ============
# 
# Data flatening
# ----------------
# 
# Here is some example data, which would eventually be sent along with a post request :
# 
#     >>> inpt = urlencode([
#     ...     ('key1', 'bla1'),
#     ...     ('key2', 'blo1'), ('key2', 'blo2'),
#     ... ])
# 
# Default behaviour for :class:`parsers.FormParser`, is to return a single value for each parameter :
# 
#     >>> (data, files) = FormParser(some_view).parse(StringIO(inpt))
#     >>> data == {'key1': 'bla1', 'key2': 'blo1'}
#     True
# 
# However, you can customize this behaviour by subclassing :class:`parsers.FormParser`, and overriding :meth:`parsers.FormParser.is_a_list` :
# 
#     >>> class MyFormParser(FormParser):
#     ... 
#     ...     def is_a_list(self, key, val_list):
#     ...         return len(val_list) > 1
# 
# This new parser only flattens the lists of parameters that contain a single value.
# 
#     >>> (data, files) = MyFormParser(some_view).parse(StringIO(inpt))
#     >>> data == {'key1': 'bla1', 'key2': ['blo1', 'blo2']}
#     True
# 
# .. note:: The same functionality is available for :class:`parsers.MultiPartParser`.
# 
# Submitting an empty list
# --------------------------
# 
# When submitting an empty select multiple, like this one ::
# 
#     <select multiple="multiple" name="key2"></select>
# 
# The browsers usually strip the parameter completely. A hack to avoid this, and therefore being able to submit an empty select multiple, is to submit a value that tells the server that the list is empty ::
# 
#     <select multiple="multiple" name="key2"><option value="_empty"></select>
# 
# :class:`parsers.FormParser` provides the server-side implementation for this hack. Considering the following posted data :
# 
#     >>> inpt = urlencode([
#     ...     ('key1', 'blo1'), ('key1', '_empty'),
#     ...     ('key2', '_empty'),
#     ... ])
# 
# :class:`parsers.FormParser` strips the values ``_empty`` from all the lists.
# 
#     >>> (data, files) = MyFormParser(some_view).parse(StringIO(inpt))
#     >>> data == {'key1': 'blo1'}
#     True
# 
# Oh ... but wait a second, the parameter ``key2`` isn't even supposed to be a list, so the parser just stripped it.
# 
#     >>> class MyFormParser(FormParser):
#     ... 
#     ...     def is_a_list(self, key, val_list):
#     ...         return key == 'key2'
#     ... 
#     >>> (data, files) = MyFormParser(some_view).parse(StringIO(inpt))
#     >>> data == {'key1': 'blo1', 'key2': []}
#     True
# 
# Better like that. Note that you can configure something else than ``_empty`` for the empty value by setting :attr:`parsers.FormParser.EMPTY_VALUE`.
# """
# import httplib, mimetypes
# from tempfile import TemporaryFile
# from django.test import TestCase
# from djangorestframework.compat import RequestFactory
# from djangorestframework.parsers import MultiPartParser
# from djangorestframework.views import View
# from StringIO import StringIO
# 
# def encode_multipart_formdata(fields, files):
#     """For testing multipart parser.
#     fields is a sequence of (name, value) elements for regular form fields.
#     files is a sequence of (name, filename, value) elements for data to be uploaded as files
#     Return (content_type, body)."""
#     BOUNDARY = '----------ThIs_Is_tHe_bouNdaRY_$'
#     CRLF = '\r\n'
#     L = []
#     for (key, value) in fields:
#         L.append('--' + BOUNDARY)
#         L.append('Content-Disposition: form-data; name="%s"' % key)
#         L.append('')
#         L.append(value)
#     for (key, filename, value) in files:
#         L.append('--' + BOUNDARY)
#         L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
#         L.append('Content-Type: %s' % get_content_type(filename))
#         L.append('')
#         L.append(value)
#     L.append('--' + BOUNDARY + '--')
#     L.append('')
#     body = CRLF.join(L)
#     content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
#     return content_type, body
# 
# def get_content_type(filename):
#     return mimetypes.guess_type(filename)[0] or 'application/octet-stream'
# 
#class TestMultiPartParser(TestCase):
#    def setUp(self):
#        self.req = RequestFactory()
#        self.content_type, self.body = encode_multipart_formdata([('key1', 'val1'), ('key1', 'val2')],
#        [('file1', 'pic.jpg', 'blablabla'), ('file1', 't.txt', 'blobloblo')])
#
#    def test_multipartparser(self):
#        """Ensure that MultiPartParser can parse multipart/form-data that contains a mix of several files and parameters."""
#        post_req = RequestFactory().post('/', self.body, content_type=self.content_type)
#        view = View()
#        view.request = post_req
#        (data, files) = MultiPartParser(view).parse(StringIO(self.body))
#        self.assertEqual(data['key1'], 'val1')
#        self.assertEqual(files['file1'].read(), 'blablabla')

from StringIO import StringIO
from cgi import parse_qs
from django import forms
from django.test import TestCase
from djangorestframework.parsers import FormParser

class Form(forms.Form):
    field1 = forms.CharField(max_length=3)
    field2 = forms.CharField()

class TestFormParser(TestCase):
    def setUp(self):
        self.string = "field1=abc&field2=defghijk"       
        
    def test_parse(self):
        """ Make sure the `QueryDict` works OK """
        parser = FormParser(None)
        
        stream = StringIO(self.string)
        (data, files) = parser.parse(stream)

        self.assertEqual(Form(data).is_valid(), True)
