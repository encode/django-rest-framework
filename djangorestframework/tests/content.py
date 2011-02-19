from django.test import TestCase
from djangorestframework.compat import RequestFactory
from djangorestframework.content import ContentMixin, StandardContentMixin, OverloadedContentMixin


class TestContentMixins(TestCase):
    def setUp(self):
        self.req = RequestFactory()

    # Interface tests

    def test_content_mixin_interface(self):
        """Ensure the ContentMixin interface is as expected."""
        self.assertRaises(NotImplementedError, ContentMixin().determine_content, None)

    def test_standard_content_mixin_interface(self):
        """Ensure the OverloadedContentMixin interface is as expected."""
        self.assertTrue(issubclass(StandardContentMixin, ContentMixin))
        getattr(StandardContentMixin, 'determine_content')

    def test_overloaded_content_mixin_interface(self):
        """Ensure the OverloadedContentMixin interface is as expected."""
        self.assertTrue(issubclass(OverloadedContentMixin, ContentMixin))
        getattr(OverloadedContentMixin, 'CONTENT_PARAM')
        getattr(OverloadedContentMixin, 'CONTENTTYPE_PARAM')
        getattr(OverloadedContentMixin, 'determine_content')

  
    # Common functionality to test with both StandardContentMixin and OverloadedContentMixin

    def ensure_determines_no_content_GET(self, mixin):
        """Ensure determine_content(request) returns None for GET request with no content."""
        request = self.req.get('/')
        self.assertEqual(mixin.determine_content(request), None)

    def ensure_determines_form_content_POST(self, mixin):
        """Ensure determine_content(request) returns content for POST request with content."""
        form_data = {'qwerty': 'uiop'}
        request = self.req.post('/', data=form_data)
        self.assertEqual(mixin.determine_content(request), (request.META['CONTENT_TYPE'], request.raw_post_data))

    def ensure_determines_non_form_content_POST(self, mixin):
        """Ensure determine_content(request) returns (content type, content) for POST request with content."""
        content = 'qwerty'
        content_type = 'text/plain'
        request = self.req.post('/', content, content_type=content_type)
        self.assertEqual(mixin.determine_content(request), (content_type, content))

    def ensure_determines_form_content_PUT(self, mixin):
        """Ensure determine_content(request) returns content for PUT request with content."""
        form_data = {'qwerty': 'uiop'}
        request = self.req.put('/', data=form_data)
        self.assertEqual(mixin.determine_content(request), (request.META['CONTENT_TYPE'], request.raw_post_data))

    def ensure_determines_non_form_content_PUT(self, mixin):
        """Ensure determine_content(request) returns (content type, content) for PUT request with content."""
        content = 'qwerty'
        content_type = 'text/plain'
        request = self.req.put('/', content, content_type=content_type)
        self.assertEqual(mixin.determine_content(request), (content_type, content))

    # StandardContentMixin behavioural tests

    def test_standard_behaviour_determines_no_content_GET(self):
        """Ensure StandardContentMixin.determine_content(request) returns None for GET request with no content."""
        self.ensure_determines_no_content_GET(StandardContentMixin())

    def test_standard_behaviour_determines_form_content_POST(self):
        """Ensure StandardContentMixin.determine_content(request) returns content for POST request with content."""
        self.ensure_determines_form_content_POST(StandardContentMixin())

    def test_standard_behaviour_determines_non_form_content_POST(self):
        """Ensure StandardContentMixin.determine_content(request) returns (content type, content) for POST request with content."""
        self.ensure_determines_non_form_content_POST(StandardContentMixin())

    def test_standard_behaviour_determines_form_content_PUT(self):
        """Ensure StandardContentMixin.determine_content(request) returns content for PUT request with content."""
        self.ensure_determines_form_content_PUT(StandardContentMixin())

    def test_standard_behaviour_determines_non_form_content_PUT(self):
        """Ensure StandardContentMixin.determine_content(request) returns (content type, content) for PUT request with content."""
        self.ensure_determines_non_form_content_PUT(StandardContentMixin())

    # OverloadedContentMixin behavioural tests

    def test_overloaded_behaviour_determines_no_content_GET(self):
        """Ensure StandardContentMixin.determine_content(request) returns None for GET request with no content."""
        self.ensure_determines_no_content_GET(OverloadedContentMixin())

    def test_overloaded_behaviour_determines_form_content_POST(self):
        """Ensure StandardContentMixin.determine_content(request) returns content for POST request with content."""
        self.ensure_determines_form_content_POST(OverloadedContentMixin())

    def test_overloaded_behaviour_determines_non_form_content_POST(self):
        """Ensure StandardContentMixin.determine_content(request) returns (content type, content) for POST request with content."""
        self.ensure_determines_non_form_content_POST(OverloadedContentMixin())

    def test_overloaded_behaviour_determines_form_content_PUT(self):
        """Ensure StandardContentMixin.determine_content(request) returns content for PUT request with content."""
        self.ensure_determines_form_content_PUT(OverloadedContentMixin())

    def test_overloaded_behaviour_determines_non_form_content_PUT(self):
        """Ensure StandardContentMixin.determine_content(request) returns (content type, content) for PUT request with content."""
        self.ensure_determines_non_form_content_PUT(OverloadedContentMixin())

    def test_overloaded_behaviour_allows_content_tunnelling(self):
        """Ensure determine_content(request) returns (content type, content) for overloaded POST request"""
        content = 'qwerty'
        content_type = 'text/plain'
        form_data = {OverloadedContentMixin.CONTENT_PARAM: content,
                     OverloadedContentMixin.CONTENTTYPE_PARAM: content_type}
        request = self.req.post('/', form_data)
        self.assertEqual(OverloadedContentMixin().determine_content(request), (content_type, content))
 
    def test_overloaded_behaviour_allows_content_tunnelling_content_type_not_set(self):
        """Ensure determine_content(request) returns (None, content) for overloaded POST request with content type not set"""
        content = 'qwerty'
        request = self.req.post('/', {OverloadedContentMixin.CONTENT_PARAM: content})
        self.assertEqual(OverloadedContentMixin().determine_content(request), (None, content))

