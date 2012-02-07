import re

from django.test import TestCase

from django.conf.urls.defaults import patterns, url
from django.test import TestCase

from djangorestframework.response import Response
from djangorestframework.views import View
from djangorestframework.renderers import BaseRenderer, JSONRenderer, YAMLRenderer, \
    XMLRenderer, JSONPRenderer, DocumentingHTMLRenderer
from djangorestframework.parsers import JSONParser, YAMLParser, XMLParser

from StringIO import StringIO
import datetime
from decimal import Decimal


_flat_repr = '{"foo": ["bar", "baz"]}'
_indented_repr = '{\n  "foo": [\n    "bar",\n    "baz"\n  ]\n}'


def strip_trailing_whitespace(content):
    """
    Seems to be some inconsistencies re. trailing whitespace with
    different versions of the json lib.
    """
    return re.sub(' +\n', '\n', content)

class JSONRendererTests(TestCase):
    """
    Tests specific to the JSON Renderer
    """

    def test_without_content_type_args(self):
        """
        Test basic JSON rendering.
        """
        obj = {'foo': ['bar', 'baz']}
        renderer = JSONRenderer(None)
        content = renderer.render(obj, 'application/json')
        # Fix failing test case which depends on version of JSON library.
        self.assertEquals(content, _flat_repr)

    def test_with_content_type_args(self):
        """
        Test JSON rendering with additional content type arguments supplied.
        """
        obj = {'foo': ['bar', 'baz']}
        renderer = JSONRenderer(None)
        content = renderer.render(obj, 'application/json; indent=2')
        self.assertEquals(strip_trailing_whitespace(content), _indented_repr)

    def test_render_and_parse(self):
        """
        Test rendering and then parsing returns the original object.
        IE obj -> render -> parse -> obj.
        """
        obj = {'foo': ['bar', 'baz']}

        renderer = JSONRenderer(None)
        parser = JSONParser(None)

        content = renderer.render(obj, 'application/json')
        (data, files) = parser.parse(StringIO(content))
        self.assertEquals(obj, data)


class MockGETView(View):

    def get(self, request, **kwargs):
        return Response({'foo': ['bar', 'baz']})


urlpatterns = patterns('',
    url(r'^jsonp/jsonrenderer$', MockGETView.as_view(renderer_classes=[JSONRenderer, JSONPRenderer])),
    url(r'^jsonp/nojsonrenderer$', MockGETView.as_view(renderer_classes=[JSONPRenderer])),
)


class JSONPRendererTests(TestCase):
    """
    Tests specific to the JSONP Renderer
    """

    urls = 'djangorestframework.tests.renderers'

    def test_without_callback_with_json_renderer(self):
        """
        Test JSONP rendering with View JSON Renderer.
        """
        resp = self.client.get('/jsonp/jsonrenderer',
                               HTTP_ACCEPT='application/json-p')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp['Content-Type'], 'application/json-p')
        self.assertEquals(resp.content, 'callback(%s);' % _flat_repr)

    def test_without_callback_without_json_renderer(self):
        """
        Test JSONP rendering without View JSON Renderer.
        """
        resp = self.client.get('/jsonp/nojsonrenderer',
                               HTTP_ACCEPT='application/json-p')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp['Content-Type'], 'application/json-p')
        self.assertEquals(resp.content, 'callback(%s);' % _flat_repr)

    def test_with_callback(self):
        """
        Test JSONP rendering with callback function name.
        """
        callback_func = 'myjsonpcallback'
        resp = self.client.get('/jsonp/nojsonrenderer?callback=' + callback_func,
                               HTTP_ACCEPT='application/json-p')
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp['Content-Type'], 'application/json-p')
        self.assertEquals(resp.content, '%s(%s);' % (callback_func, _flat_repr))


if YAMLRenderer:
    _yaml_repr = 'foo: [bar, baz]\n'

    class YAMLRendererTests(TestCase):
        """
        Tests specific to the JSON Renderer
        """

        def test_render(self):
            """
            Test basic YAML rendering.
            """
            obj = {'foo': ['bar', 'baz']}
            renderer = YAMLRenderer(None)
            content = renderer.render(obj, 'application/yaml')
            self.assertEquals(content, _yaml_repr)

        def test_render_and_parse(self):
            """
            Test rendering and then parsing returns the original object.
            IE obj -> render -> parse -> obj.
            """
            obj = {'foo': ['bar', 'baz']}

            renderer = YAMLRenderer(None)
            parser = YAMLParser(None)

            content = renderer.render(obj, 'application/yaml')
            (data, files) = parser.parse(StringIO(content))
            self.assertEquals(obj, data)



class XMLRendererTestCase(TestCase):
    """
    Tests specific to the XML Renderer
    """

    _complex_data = {
        "creation_date": datetime.datetime(2011, 12, 25, 12, 45, 00), 
        "name": "name", 
        "sub_data_list": [
            {
                "sub_id": 1, 
                "sub_name": "first"
            }, 
            {
                "sub_id": 2, 
                "sub_name": "second"
            }
        ]
    }

    def test_render_string(self):
        """
        Test XML rendering.
        """
        renderer = XMLRenderer(None)
        content = renderer.render({'field': 'astring'}, 'application/xml')
        self.assertXMLContains(content, '<field>astring</field>')

    def test_render_integer(self):
        """
        Test XML rendering.
        """
        renderer = XMLRenderer(None)
        content = renderer.render({'field': 111}, 'application/xml')
        self.assertXMLContains(content, '<field>111</field>')

    def test_render_datetime(self):
        """
        Test XML rendering.
        """
        renderer = XMLRenderer(None)
        content = renderer.render({
            'field': datetime.datetime(2011, 12, 25, 12, 45, 00)
        }, 'application/xml')
        self.assertXMLContains(content, '<field>2011-12-25 12:45:00</field>')

    def test_render_float(self):
        """
        Test XML rendering.
        """
        renderer = XMLRenderer(None)
        content = renderer.render({'field': 123.4}, 'application/xml')
        self.assertXMLContains(content, '<field>123.4</field>')

    def test_render_decimal(self):
        """
        Test XML rendering.
        """
        renderer = XMLRenderer(None)
        content = renderer.render({'field': Decimal('111.2')}, 'application/xml')
        self.assertXMLContains(content, '<field>111.2</field>')

    def test_render_none(self):
        """
        Test XML rendering.
        """
        renderer = XMLRenderer(None)
        content = renderer.render({'field': None}, 'application/xml')
        self.assertXMLContains(content, '<field></field>')
        
    def test_render_complex_data(self):
        """
        Test XML rendering.
        """
        renderer = XMLRenderer(None)            
        content = renderer.render(self._complex_data, 'application/xml')
        self.assertXMLContains(content, '<sub_name>first</sub_name>')
        self.assertXMLContains(content, '<sub_name>second</sub_name>')

    def test_render_and_parse_complex_data(self):
        """
        Test XML rendering.
        """
        renderer = XMLRenderer(None)            
        content = StringIO(renderer.render(self._complex_data, 'application/xml'))
        
        parser = XMLParser(None)
        complex_data_out, dummy = parser.parse(content)
        error_msg = "complex data differs!IN:\n %s \n\n OUT:\n %s" % (repr(self._complex_data), repr(complex_data_out))
        self.assertEqual(self._complex_data, complex_data_out, error_msg)

    def assertXMLContains(self, xml, string):
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="utf-8"?>\n<root>'))
        self.assertTrue(xml.endswith('</root>'))
        self.assertTrue(string in xml, '%r not in %r' % (string, xml))

