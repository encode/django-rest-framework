# TODO: refactor these tests
from django.test import TestCase
from djangorestframework.compat import RequestFactory
from djangorestframework.request import RequestMixin
from djangorestframework.parsers import FormParser, MultipartParser
#from djangorestframework.content import ContentMixin, StandardContentMixin, OverloadedContentMixin
#
#
class TestContentMixins(TestCase):
    def setUp(self):
        self.req = RequestFactory()

#    # Interface tests
#
#    def test_content_mixin_interface(self):
#        """Ensure the ContentMixin interface is as expected."""
#        self.assertRaises(NotImplementedError, ContentMixin().determine_content, None)
#
#    def test_standard_content_mixin_interface(self):
#        """Ensure the OverloadedContentMixin interface is as expected."""
#        self.assertTrue(issubclass(StandardContentMixin, ContentMixin))
#        getattr(StandardContentMixin, 'determine_content')
#
#    def test_overloaded_content_mixin_interface(self):
#        """Ensure the OverloadedContentMixin interface is as expected."""
#        self.assertTrue(issubclass(OverloadedContentMixin, ContentMixin))
#        getattr(OverloadedContentMixin, 'CONTENT_PARAM')
#        getattr(OverloadedContentMixin, 'CONTENTTYPE_PARAM')
#        getattr(OverloadedContentMixin, 'determine_content')
#
#  
#    # Common functionality to test with both StandardContentMixin and OverloadedContentMixin
#
    def ensure_determines_no_content_GET(self, view):
        """Ensure view.RAW_CONTENT returns None for GET request with no content."""
        view.request = self.req.get('/')
        self.assertEqual(view.RAW_CONTENT, None)

    def ensure_determines_form_content_POST(self, view):
        """Ensure view.RAW_CONTENT returns content for POST request with form content."""
        form_data = {'qwerty': 'uiop'}
        view.parsers = (FormParser, MultipartParser)
        view.request = self.req.post('/', data=form_data)
        self.assertEqual(view.RAW_CONTENT, form_data)

    def ensure_determines_non_form_content_POST(self, mixin):
        """Ensure view.RAW_CONTENT returns content for POST request with non-form content."""
        content = 'qwerty'
        content_type = 'text/plain'
        view.parsers = (PlainTextParser,)
        view.request = self.req.post('/', content, content_type=content_type)
        self.assertEqual(view.RAW_CONTENT, form_data)

    def ensure_determines_form_content_PUT(self, mixin):
        """Ensure view.RAW_CONTENT returns content for PUT request with form content."""
        form_data = {'qwerty': 'uiop'}
        view.parsers = (FormParser, MultipartParser)
        view.request = self.req.put('/', data=form_data)
        self.assertEqual(view.RAW_CONTENT, form_data)

    def ensure_determines_non_form_content_PUT(self, mixin):
        """Ensure view.RAW_CONTENT returns content for PUT request with non-form content."""
        content = 'qwerty'
        content_type = 'text/plain'
        view.parsers = (PlainTextParser,)
        view.request = self.req.post('/', content, content_type=content_type)
        self.assertEqual(view.RAW_CONTENT, form_data)#

    def test_standard_behaviour_determines_no_content_GET(self):
        """Ensure request.RAW_CONTENT returns None for GET request with no content."""
        self.ensure_determines_no_content_GET(RequestMixin())

    def test_standard_behaviour_determines_form_content_POST(self):
        """Ensure request.RAW_CONTENT returns content for POST request with form content."""
        self.ensure_determines_form_content_POST(RequestMixin())

    def test_standard_behaviour_determines_non_form_content_POST(self):
        """Ensure StandardContentMixin.determine_content(request) returns (content type, content) for POST request with content."""
        self.ensure_determines_non_form_content_POST(RequestMixin())

    def test_standard_behaviour_determines_form_content_PUT(self):
        """Ensure StandardContentMixin.determine_content(request) returns content for PUT request with content."""
        self.ensure_determines_form_content_PUT(RequestMixin())

#    def test_standard_behaviour_determines_non_form_content_PUT(self):
#        """Ensure StandardContentMixin.determine_content(request) returns (content type, content) for PUT request with content."""
#        self.ensure_determines_non_form_content_PUT(StandardContentMixin())
#
#    # OverloadedContentMixin behavioural tests
#
#    def test_overloaded_behaviour_determines_no_content_GET(self):
#        """Ensure StandardContentMixin.determine_content(request) returns None for GET request with no content."""
#        self.ensure_determines_no_content_GET(OverloadedContentMixin())
#
#    def test_overloaded_behaviour_determines_form_content_POST(self):
#        """Ensure StandardContentMixin.determine_content(request) returns content for POST request with content."""
#        self.ensure_determines_form_content_POST(OverloadedContentMixin())
#
#    def test_overloaded_behaviour_determines_non_form_content_POST(self):
#        """Ensure StandardContentMixin.determine_content(request) returns (content type, content) for POST request with content."""
#        self.ensure_determines_non_form_content_POST(OverloadedContentMixin())
#
#    def test_overloaded_behaviour_determines_form_content_PUT(self):
#        """Ensure StandardContentMixin.determine_content(request) returns content for PUT request with content."""
#        self.ensure_determines_form_content_PUT(OverloadedContentMixin())
#
#    def test_overloaded_behaviour_determines_non_form_content_PUT(self):
#        """Ensure StandardContentMixin.determine_content(request) returns (content type, content) for PUT request with content."""
#        self.ensure_determines_non_form_content_PUT(OverloadedContentMixin())
#
#    def test_overloaded_behaviour_allows_content_tunnelling(self):
#        """Ensure determine_content(request) returns (content type, content) for overloaded POST request"""
#        content = 'qwerty'
#        content_type = 'text/plain'
#        form_data = {OverloadedContentMixin.CONTENT_PARAM: content,
#                     OverloadedContentMixin.CONTENTTYPE_PARAM: content_type}
#        request = self.req.post('/', form_data)
#        self.assertEqual(OverloadedContentMixin().determine_content(request), (content_type, content))
#        self.assertEqual(request.META['CONTENT_TYPE'], content_type)
# 
#    def test_overloaded_behaviour_allows_content_tunnelling_content_type_not_set(self):
#        """Ensure determine_content(request) returns (None, content) for overloaded POST request with content type not set"""
#        content = 'qwerty'
#        request = self.req.post('/', {OverloadedContentMixin.CONTENT_PARAM: content})
#        self.assertEqual(OverloadedContentMixin().determine_content(request), (None, content))

