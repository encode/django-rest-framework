# encoding: utf-8
from __future__ import unicode_literals

from django.test import TestCase

from rest_framework.relations import Hyperlink
from rest_framework.templatetags.rest_framework import (
    add_nested_class, add_query_param, format_value, urlize_quoted_links
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


class Issue1386Tests(TestCase):
    """
    Covers #1386
    """

    def test_issue_1386(self):
        """
        Test function urlize_quoted_links with different args
        """
        correct_urls = [
            "asdf.com",
            "asdf.net",
            "www.as_df.org",
            "as.d8f.ghj8.gov",
        ]
        for i in correct_urls:
            res = urlize_quoted_links(i)
            self.assertNotEqual(res, i)
            self.assertIn(i, res)

        incorrect_urls = [
            "mailto://asdf@fdf.com",
            "asdf.netnet",
        ]
        for i in incorrect_urls:
            res = urlize_quoted_links(i)
            self.assertEqual(i, res)

        # example from issue #1386, this shouldn't raise an exception
        urlize_quoted_links("asdf:[/p]zxcv.com")


class URLizerTests(TestCase):
    """
    Test if JSON URLs are transformed into links well
    """
    def _urlize_dict_check(self, data):
        """
        For all items in dict test assert that the value is urlized key
        """
        for original, urlized in data.items():
            assert urlize_quoted_links(original, nofollow=False) == urlized

    def test_json_with_url(self):
        """
        Test if JSON URLs are transformed into links well
        """
        data = {}
        data['"url": "http://api/users/1/", '] = \
            '&quot;url&quot;: &quot;<a href="http://api/users/1/">http://api/users/1/</a>&quot;, '
        data['"foo_set": [\n    "http://api/foos/1/"\n], '] = \
            '&quot;foo_set&quot;: [\n    &quot;<a href="http://api/foos/1/">http://api/foos/1/</a>&quot;\n], '
        self._urlize_dict_check(data)
