"""Test a range of REST API usage of the example application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from blogpost import views
#import json
#from rest.utils import xml2dict, dict2xml


class AcceptHeaderTests(TestCase):
    """Test correct behaviour of the Accept header as specified by RFC 2616:

    http://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.1"""

    def assert_accept_mimetype(self, mimetype, expect=None):
        """Assert that a request with given mimetype in the accept header,
        gives a response with the appropriate content-type."""
        if expect is None:
            expect = mimetype

        resp = self.client.get(reverse(views.RootResource), HTTP_ACCEPT=mimetype)

        self.assertEquals(resp['content-type'], expect)


    def test_accept_json(self):
        """Ensure server responds with Content-Type of JSON when requested."""
        self.assert_accept_mimetype('application/json')

    def test_accept_xml(self):
        """Ensure server responds with Content-Type of XML when requested."""
        self.assert_accept_mimetype('application/xml')

    def test_accept_json_when_prefered_to_xml(self):
        """Ensure server responds with Content-Type of JSON when it is the client's prefered choice."""
        self.assert_accept_mimetype('application/json;q=0.9, application/xml;q=0.1', expect='application/json')

    def test_accept_xml_when_prefered_to_json(self):
        """Ensure server responds with Content-Type of XML when it is the client's prefered choice."""
        self.assert_accept_mimetype('application/json;q=0.1, application/xml;q=0.9', expect='application/xml')

    def test_default_json_prefered(self):
        """Ensure server responds with JSON in preference to XML."""
        self.assert_accept_mimetype('application/json,application/xml', expect='application/json')

    def test_accept_generic_subtype_format(self):
        """Ensure server responds with an appropriate type, when the subtype is left generic."""
        self.assert_accept_mimetype('text/*', expect='text/html')

    def test_accept_generic_type_format(self):
        """Ensure server responds with an appropriate type, when the type and subtype are left generic."""
        self.assert_accept_mimetype('*/*', expect='application/json')

    def test_invalid_accept_header_returns_406(self):
        """Ensure server returns a 406 (not acceptable) response if we set the Accept header to junk."""
        resp = self.client.get(reverse(views.RootResource), HTTP_ACCEPT='invalid/invalid')
        self.assertNotEquals(resp['content-type'], 'invalid/invalid')
        self.assertEquals(resp.status_code, 406)
    
    def test_prefer_specific_over_generic(self):   # This test is broken right now
        """More specific accept types have precedence over less specific types."""
        self.assert_accept_mimetype('application/xml, */*', expect='application/xml')
        self.assert_accept_mimetype('*/*, application/xml', expect='application/xml')


class AllowedMethodsTests(TestCase):
    """Basic tests to check that only allowed operations may be performed on a Resource"""

    def test_reading_a_read_only_resource_is_allowed(self):
        """GET requests on a read only resource should default to a 200 (OK) response"""
        resp = self.client.get(reverse(views.RootResource))
        self.assertEquals(resp.status_code, 200)
        
    def test_writing_to_read_only_resource_is_not_allowed(self):
        """PUT requests on a read only resource should default to a 405 (method not allowed) response"""
        resp = self.client.put(reverse(views.RootResource), {})
        self.assertEquals(resp.status_code, 405)
#
#    def test_reading_write_only_not_allowed(self):
#        resp = self.client.get(reverse(views.WriteOnlyResource))
#        self.assertEquals(resp.status_code, 405)
#
#    def test_writing_write_only_allowed(self):
#        resp = self.client.put(reverse(views.WriteOnlyResource), {})
#        self.assertEquals(resp.status_code, 200)
#
#
#class EncodeDecodeTests(TestCase):
#    def setUp(self):
#        super(self.__class__, self).setUp()
#        self.input = {'a': 1, 'b': 'example'}
#
#    def test_encode_form_decode_json(self):
#        content = self.input
#        resp = self.client.put(reverse(views.WriteOnlyResource), content)
#        output = json.loads(resp.content)
#        self.assertEquals(self.input, output)
#
#    def test_encode_json_decode_json(self):
#        content = json.dumps(self.input)
#        resp = self.client.put(reverse(views.WriteOnlyResource), content, 'application/json')
#        output = json.loads(resp.content)
#        self.assertEquals(self.input, output)
#
#    #def test_encode_xml_decode_json(self):
#    #    content = dict2xml(self.input)
#    #    resp = self.client.put(reverse(views.WriteOnlyResource), content, 'application/json', HTTP_ACCEPT='application/json')
#    #    output = json.loads(resp.content)
#    #    self.assertEquals(self.input, output)
#
#    #def test_encode_form_decode_xml(self):
#    #    content = self.input
#    #    resp = self.client.put(reverse(views.WriteOnlyResource), content, HTTP_ACCEPT='application/xml')
#    #    output = xml2dict(resp.content)
#    #    self.assertEquals(self.input, output)
#
#    #def test_encode_json_decode_xml(self):
#    #    content = json.dumps(self.input)
#    #    resp = self.client.put(reverse(views.WriteOnlyResource), content, 'application/json', HTTP_ACCEPT='application/xml')
#    #    output = xml2dict(resp.content)
#    #    self.assertEquals(self.input, output)
#
#    #def test_encode_xml_decode_xml(self):
#    #    content = dict2xml(self.input)
#    #    resp = self.client.put(reverse(views.WriteOnlyResource), content, 'application/json', HTTP_ACCEPT='application/xml')
#    #    output = xml2dict(resp.content)
#    #    self.assertEquals(self.input, output)
#
#class ModelTests(TestCase):
#    def test_create_container(self):
#        content = json.dumps({'name': 'example'})
#        resp = self.client.post(reverse(views.ContainerFactory), content, 'application/json')
#        output = json.loads(resp.content)
#        self.assertEquals(resp.status_code, 201)
#        self.assertEquals(output['name'], 'example')
#        self.assertEquals(set(output.keys()), set(('absolute_uri', 'name', 'key')))
#
#class CreatedModelTests(TestCase):
#    def setUp(self):
#        content = json.dumps({'name': 'example'})
#        resp = self.client.post(reverse(views.ContainerFactory), content, 'application/json', HTTP_ACCEPT='application/json')
#        self.container = json.loads(resp.content)
#
#    def test_read_container(self):
#        resp = self.client.get(self.container["absolute_uri"])
#        self.assertEquals(resp.status_code, 200)
#        container = json.loads(resp.content)
#        self.assertEquals(container, self.container)
#
#    def test_delete_container(self):
#        resp = self.client.delete(self.container["absolute_uri"])
#        self.assertEquals(resp.status_code, 204)
#        self.assertEquals(resp.content, '')
#
#    def test_update_container(self):
#        self.container['name'] = 'new'
#        content = json.dumps(self.container)
#        resp = self.client.put(self.container["absolute_uri"], content, 'application/json')
#        self.assertEquals(resp.status_code, 200)
#        container = json.loads(resp.content)
#        self.assertEquals(container, self.container)

