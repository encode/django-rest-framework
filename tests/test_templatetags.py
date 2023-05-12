import unittest

from django.template import Context, Template
from django.test import TestCase
from django.utils.html import urlize

from rest_framework.compat import coreapi, coreschema
from rest_framework.relations import Hyperlink
from rest_framework.templatetags import rest_framework
from rest_framework.templatetags.rest_framework import (
    add_nested_class, add_query_param, as_string, break_long_headers,
    format_value, get_pagination_html, schema_links
)
from rest_framework.test import APIRequestFactory

factory = APIRequestFactory()


def format_html(html):
    """
    Helper function that formats HTML in order for easier comparison
    :param html: raw HTML text to be formatted
    :return: Cleaned HTML with no newlines or spaces
    """
    return html.replace('\n', '').replace(' ', '')


class TemplateTagTests(TestCase):

    def test_add_query_param_with_non_latin_character(self):
        # Ensure we don't double-escape non-latin characters
        # that are present in the querystring.
        # See #1314.
        request = factory.get("/", {'q': '查询'})
        json_url = add_query_param(request, "format", "json")
        self.assertIn("q=%E6%9F%A5%E8%AF%A2", json_url)
        self.assertIn("format=json", json_url)

    def test_format_value_boolean_or_none(self):
        """
        Tests format_value with booleans and None
        """
        self.assertEqual(format_value(True), '<code>true</code>')
        self.assertEqual(format_value(False), '<code>false</code>')
        self.assertEqual(format_value(None), '<code>null</code>')

    def test_format_value_hyperlink(self):
        """
        Tests format_value with a URL
        """
        url = 'http://url.com'
        name = 'name_of_url'
        hyperlink = Hyperlink(url, name)
        self.assertEqual(format_value(hyperlink), '<a href=%s>%s</a>' % (url, name))

    def test_format_value_list(self):
        """
        Tests format_value with a list of strings
        """
        list_items = ['item1', 'item2', 'item3']
        self.assertEqual(format_value(list_items), '\n item1, item2, item3\n')
        self.assertEqual(format_value([]), '\n\n')

    def test_format_value_dict(self):
        """
        Tests format_value with a dict
        """
        test_dict = {'a': 'b'}
        expected_dict_format = """
        <table class="table table-striped">
            <tbody>
                <tr>
                    <th>a</th>
                    <td>b</td>
                </tr>
            </tbody>
        </table>"""
        self.assertEqual(
            format_html(format_value(test_dict)),
            format_html(expected_dict_format)
        )

    def test_format_value_table(self):
        """
        Tests format_value with a list of lists/dicts
        """
        list_of_lists = [['list1'], ['list2'], ['list3']]
        expected_list_format = """
        <tableclass="tabletable-striped">
            <tbody>
               <tr>
                  <th>0</th>
                  <td>list1</td>
               </tr>
               <tr>
                  <th>1</th>
                  <td>list2</td>
               </tr>
               <tr>
                  <th>2</th>
                  <td>list3</td>
               </tr>
            </tbody>
            </table>"""
        self.assertEqual(
            format_html(format_value(list_of_lists)),
            format_html(expected_list_format)
        )

        expected_dict_format = """
        <tableclass="tabletable-striped">
            <tbody>
                <tr>
                    <th>0</th>
                    <td>
                        <tableclass="tabletable-striped">
                            <tbody>
                                <tr>
                                    <th>item1</th>
                                    <td>value1</td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
                <tr>
                    <th>1</th>
                    <td>
                        <tableclass="tabletable-striped">
                            <tbody>
                                <tr>
                                    <th>item2</th>
                                    <td>value2</td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
                <tr>
                    <th>2</th>
                    <td>
                        <tableclass="tabletable-striped">
                            <tbody>
                                <tr>
                                    <th>item3</th>
                                    <td>value3</td>
                                </tr>
                            </tbody>
                        </table>
                    </td>
                </tr>
            </tbody>
        </table>"""

        list_of_dicts = [{'item1': 'value1'}, {'item2': 'value2'}, {'item3': 'value3'}]
        self.assertEqual(
            format_html(format_value(list_of_dicts)),
            format_html(expected_dict_format)
        )

    def test_format_value_simple_string(self):
        """
        Tests format_value with a simple string
        """
        simple_string = 'this is an example of a string'
        self.assertEqual(format_value(simple_string), simple_string)

    def test_format_value_string_hyperlink(self):
        """
        Tests format_value with a url
        """
        url = 'http://www.example.com'
        self.assertEqual(format_value(url), '<a href="http://www.example.com">http://www.example.com</a>')

    def test_format_value_string_email(self):
        """
        Tests format_value with an email address
        """
        email = 'something@somewhere.com'
        self.assertEqual(format_value(email), '<a href="mailto:something@somewhere.com">something@somewhere.com</a>')

    def test_format_value_string_newlines(self):
        """
        Tests format_value with a string with newline characters
        :return:
        """
        text = 'Dear user, \n this is a message \n from,\nsomeone'
        self.assertEqual(format_value(text), '<pre>Dear user, \n this is a message \n from,\nsomeone</pre>')

    def test_format_value_object(self):
        """
        Tests that format_value with a object returns the object's __str__ method
        """
        obj = object()
        self.assertEqual(format_value(obj), obj.__str__())

    def test_add_nested_class(self):
        """
        Tests that add_nested_class returns the proper class
        """
        positive_cases = [
            [['item']],
            [{'item1': 'value1'}],
            {'item1': 'value1'}
        ]

        negative_cases = [
            ['list'],
            '',
            None,
            True,
            False
        ]

        for case in positive_cases:
            self.assertEqual(add_nested_class(case), 'class=nested')

        for case in negative_cases:
            self.assertEqual(add_nested_class(case), '')

    def test_as_string_with_none(self):
        result = as_string(None)
        assert result == ''

    def test_get_pagination_html(self):
        class MockPager:
            def __init__(self):
                self.called = False

            def to_html(self):
                self.called = True

        pager = MockPager()
        get_pagination_html(pager)
        assert pager.called is True

    def test_break_long_lines(self):
        header = 'long test header,' * 20
        expected_header = '<br> ' + ', <br>'.join(header.split(','))
        assert break_long_headers(header) == expected_header


class Issue1386Tests(TestCase):
    """
    Covers #1386
    """

    def test_issue_1386(self):
        """
        Test function urlize with different args
        """
        correct_urls = [
            "asdf.com",
            "asdf.net",
            "www.as_df.org",
            "as.d8f.ghj8.gov",
        ]
        for i in correct_urls:
            res = urlize(i)
            self.assertNotEqual(res, i)
            self.assertIn(i, res)

        incorrect_urls = [
            "mailto://asdf@fdf.com",
            "asdf.netnet",
        ]
        for i in incorrect_urls:
            res = urlize(i)
            self.assertEqual(i, res)

        # example from issue #1386, this shouldn't raise an exception
        urlize("asdf:[/p]zxcv.com")

    def test_smart_urlquote_wrapper_handles_value_error(self):
        def mock_smart_urlquote(url):
            raise ValueError

        old = rest_framework.smart_urlquote
        rest_framework.smart_urlquote = mock_smart_urlquote
        assert rest_framework.smart_urlquote_wrapper('test') is None
        rest_framework.smart_urlquote = old


class URLizerTests(TestCase):
    """
    Test if JSON URLs are transformed into links well
    """
    def _urlize_dict_check(self, data):
        """
        For all items in dict test assert that the value is urlized key
        """
        for original, urlized in data.items():
            assert urlize(original, nofollow=False) == urlized

    def test_json_with_url(self):
        """
        Test if JSON URLs are transformed into links well
        """
        data = {}
        data['"url": "http://api/users/1/", '] = \
            '"url": "<a href="http://api/users/1/">http://api/users/1/</a>", '
        data['"foo_set": [\n    "http://api/foos/1/"\n], '] = \
            '"foo_set": [\n    "<a href="http://api/foos/1/">http://api/foos/1/</a>"\n], '
        self._urlize_dict_check(data)

    def test_template_render_with_autoescape(self):
        """
        Test that HTML is correctly escaped in Browsable API views.
        """
        template = Template("{% load rest_framework %}{{ content|urlize }}")
        rendered = template.render(Context({'content': '<script>alert()</script> http://example.com'}))
        assert rendered == '&lt;script&gt;alert()&lt;/script&gt;' \
                           ' <a href="http://example.com" rel="nofollow">http://example.com</a>'

    def test_template_render_with_noautoescape(self):
        """
        Test if the autoescape value is getting passed to urlize filter.
        """
        template = Template("{% load rest_framework %}"
                            "{% autoescape off %}{{ content|urlize }}"
                            "{% endautoescape %}")
        rendered = template.render(Context({'content': '<b> "http://example.com" </b>'}))
        assert rendered == '<b> "<a href="http://example.com" rel="nofollow">http://example.com</a>" </b>'


@unittest.skipUnless(coreapi, 'coreapi is not installed')
class SchemaLinksTests(TestCase):

    def test_schema_with_empty_links(self):
        schema = coreapi.Document(
            url='',
            title='Example API',
            content={
                'users': {
                    'list': {}
                }
            }
        )
        section = schema['users']
        flat_links = schema_links(section)
        assert len(flat_links) == 0

    def test_single_action(self):
        schema = coreapi.Document(
            url='',
            title='Example API',
            content={
                'users': {
                    'list': coreapi.Link(
                        url='/users/',
                        action='get',
                        fields=[]
                    )
                }
            }
        )
        section = schema['users']
        flat_links = schema_links(section)
        assert len(flat_links) == 1
        assert 'list' in flat_links

    def test_default_actions(self):
        schema = coreapi.Document(
            url='',
            title='Example API',
            content={
                'users': {
                    'create': coreapi.Link(
                        url='/users/',
                        action='post',
                        fields=[]
                    ),
                    'list': coreapi.Link(
                        url='/users/',
                        action='get',
                        fields=[]
                    ),
                    'read': coreapi.Link(
                        url='/users/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    ),
                    'update': coreapi.Link(
                        url='/users/{id}/',
                        action='patch',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    )
                }
            }
        )
        section = schema['users']
        flat_links = schema_links(section)
        assert len(flat_links) == 4
        assert 'list' in flat_links
        assert 'create' in flat_links
        assert 'read' in flat_links
        assert 'update' in flat_links

    def test_default_actions_and_single_custom_action(self):
        schema = coreapi.Document(
            url='',
            title='Example API',
            content={
                'users': {
                    'create': coreapi.Link(
                        url='/users/',
                        action='post',
                        fields=[]
                    ),
                    'list': coreapi.Link(
                        url='/users/',
                        action='get',
                        fields=[]
                    ),
                    'read': coreapi.Link(
                        url='/users/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    ),
                    'update': coreapi.Link(
                        url='/users/{id}/',
                        action='patch',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    ),
                    'friends': coreapi.Link(
                        url='/users/{id}/friends',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    )
                }
            }
        )
        section = schema['users']
        flat_links = schema_links(section)
        assert len(flat_links) == 5
        assert 'list' in flat_links
        assert 'create' in flat_links
        assert 'read' in flat_links
        assert 'update' in flat_links
        assert 'friends' in flat_links

    def test_default_actions_and_single_custom_action_two_methods(self):
        schema = coreapi.Document(
            url='',
            title='Example API',
            content={
                'users': {
                    'create': coreapi.Link(
                        url='/users/',
                        action='post',
                        fields=[]
                    ),
                    'list': coreapi.Link(
                        url='/users/',
                        action='get',
                        fields=[]
                    ),
                    'read': coreapi.Link(
                        url='/users/{id}/',
                        action='get',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    ),
                    'update': coreapi.Link(
                        url='/users/{id}/',
                        action='patch',
                        fields=[
                            coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                        ]
                    ),
                    'friends': {
                        'list': coreapi.Link(
                            url='/users/{id}/friends',
                            action='get',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        ),
                        'create': coreapi.Link(
                            url='/users/{id}/friends',
                            action='post',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        )
                    }
                }
            }
        )
        section = schema['users']
        flat_links = schema_links(section)
        assert len(flat_links) == 6
        assert 'list' in flat_links
        assert 'create' in flat_links
        assert 'read' in flat_links
        assert 'update' in flat_links
        assert 'friends > list' in flat_links
        assert 'friends > create' in flat_links

    def test_multiple_nested_routes(self):
        schema = coreapi.Document(
            url='',
            title='Example API',
            content={
                'animals': {
                    'dog': {
                        'vet': {
                            'list': coreapi.Link(
                                url='/animals/dog/{id}/vet',
                                action='get',
                                fields=[
                                    coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                                ]
                            )
                        },
                        'read': coreapi.Link(
                            url='/animals/dog/{id}',
                            action='get',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        )
                    },
                    'cat': {
                        'list': coreapi.Link(
                            url='/animals/cat/',
                            action='get',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        ),
                        'create': coreapi.Link(
                            url='/animals/cat',
                            action='post',
                            fields=[]
                        )
                    }
                }
            }
        )
        section = schema['animals']
        flat_links = schema_links(section)
        assert len(flat_links) == 4
        assert 'cat > create' in flat_links
        assert 'cat > list' in flat_links
        assert 'dog > read' in flat_links
        assert 'dog > vet > list' in flat_links

    def test_multiple_resources_with_multiple_nested_routes(self):
        schema = coreapi.Document(
            url='',
            title='Example API',
            content={
                'animals': {
                    'dog': {
                        'vet': {
                            'list': coreapi.Link(
                                url='/animals/dog/{id}/vet',
                                action='get',
                                fields=[
                                    coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                                ]
                            )
                        },
                        'read': coreapi.Link(
                            url='/animals/dog/{id}',
                            action='get',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        )
                    },
                    'cat': {
                        'list': coreapi.Link(
                            url='/animals/cat/',
                            action='get',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        ),
                        'create': coreapi.Link(
                            url='/animals/cat',
                            action='post',
                            fields=[]
                        )
                    }
                },
                'farmers': {
                    'silo': {
                        'soy': {
                            'list': coreapi.Link(
                                url='/farmers/silo/{id}/soy',
                                action='get',
                                fields=[
                                    coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                                ]
                            )
                        },
                        'list': coreapi.Link(
                            url='/farmers/silo',
                            action='get',
                            fields=[
                                coreapi.Field('id', required=True, location='path', schema=coreschema.String())
                            ]
                        )
                    }
                }
            }
        )
        section = schema['animals']
        flat_links = schema_links(section)
        assert len(flat_links) == 4
        assert 'cat > create' in flat_links
        assert 'cat > list' in flat_links
        assert 'dog > read' in flat_links
        assert 'dog > vet > list' in flat_links

        section = schema['farmers']
        flat_links = schema_links(section)
        assert len(flat_links) == 2
        assert 'silo > list' in flat_links
        assert 'silo > soy > list' in flat_links
