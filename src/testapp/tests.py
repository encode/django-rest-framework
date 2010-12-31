"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from testapp import views
import json
from rest.utils import xml2dict, dict2xml

class AcceptHeaderTests(TestCase):
    def assert_accept_mimetype(self, mimetype, expect=None, expect_match=True):
        """
        Assert that a request with given mimetype in the accept header,
        gives a response with the appropriate content-type.
        """
        if expect is None:
            expect = mimetype

        resp = self.client.get(reverse(views.ReadOnlyResource), HTTP_ACCEPT=mimetype)

        if expect_match:
            self.assertEquals(resp['content-type'], expect)
        else:
            self.assertNotEquals(resp['content-type'], expect)

    def test_accept_xml(self):
        self.assert_accept_mimetype('application/xml')

    def test_accept_json(self):
        self.assert_accept_mimetype('application/json')

    def test_accept_xml_prefered_to_json(self):
        self.assert_accept_mimetype('application/xml,q=0.9;application/json,q=0.1', expect='application/xml')

    def test_accept_json_prefered_to_xml(self):
        self.assert_accept_mimetype('application/json,q=0.9;application/xml,q=0.1', expect='application/json')

    def test_dont_accept_invalid(self):
        self.assert_accept_mimetype('application/invalid', expect_match=False)

    def test_invalid_accept_header_returns_406(self):
        resp = self.client.get(reverse(views.ReadOnlyResource), HTTP_ACCEPT='invalid/invalid')
        self.assertEquals(resp.status_code, 406)

class AllowedMethodsTests(TestCase):
    def test_reading_read_only_allowed(self):
        resp = self.client.get(reverse(views.ReadOnlyResource))
        self.assertEquals(resp.status_code, 200)
        
    def test_writing_read_only_not_allowed(self):
        resp = self.client.put(reverse(views.ReadOnlyResource), {})
        self.assertEquals(resp.status_code, 405)

    def test_reading_write_only_not_allowed(self):
        resp = self.client.get(reverse(views.WriteOnlyResource))
        self.assertEquals(resp.status_code, 405)

    def test_writing_write_only_allowed(self):
        resp = self.client.put(reverse(views.WriteOnlyResource), {})
        self.assertEquals(resp.status_code, 200)

class EncodeDecodeTests(TestCase):
    def setUp(self):
        super(self.__class__, self).setUp()
        self.input = {'a': 1, 'b': 'example'}

    def test_encode_form_decode_json(self):
        content = self.input
        resp = self.client.put(reverse(views.WriteOnlyResource), content, HTTP_ACCEPT='application/json')
        output = json.loads(resp.content)
        self.assertEquals(self.input, output)

    def test_encode_json_decode_json(self):
        content = json.dumps(self.input)
        resp = self.client.put(reverse(views.WriteOnlyResource), content, 'application/json', HTTP_ACCEPT='application/json')
        output = json.loads(resp.content)
        self.assertEquals(self.input, output)

    def test_encode_xml_decode_json(self):
        content = dict2xml(self.input)
        resp = self.client.put(reverse(views.WriteOnlyResource), content, 'application/json', HTTP_ACCEPT='application/json')
        output = json.loads(resp.content)
        self.assertEquals(self.input, output)

    def test_encode_form_decode_xml(self):
        content = self.input
        resp = self.client.put(reverse(views.WriteOnlyResource), content, HTTP_ACCEPT='application/xml')
        output = xml2dict(resp.content)
        self.assertEquals(self.input, output)

    def test_encode_json_decode_xml(self):
        content = json.dumps(self.input)
        resp = self.client.put(reverse(views.WriteOnlyResource), content, 'application/json', HTTP_ACCEPT='application/xml')
        output = xml2dict(resp.content)
        self.assertEquals(self.input, output)

    def test_encode_xml_decode_xml(self):
        content = dict2xml(self.input)
        resp = self.client.put(reverse(views.WriteOnlyResource), content, 'application/json', HTTP_ACCEPT='application/xml')
        output = xml2dict(resp.content)
        self.assertEquals(self.input, output)