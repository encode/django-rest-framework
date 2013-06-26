# -- coding: utf-8 --

from __future__ import unicode_literals
from django.test import TestCase
from rest_framework.views import APIView
from rest_framework.compat import apply_markdown, smart_text
from rest_framework.utils.formatting import get_view_name, get_view_description

# We check that docstrings get nicely un-indented.
DESCRIPTION = """an example docstring
====================

* list
* list

another header
--------------

    code block

indented

# hash style header #"""

# If markdown is installed we also test it's working
# (and that our wrapped forces '=' to h2 and '-' to h3)

# We support markdown < 2.1 and markdown >= 2.1
MARKED_DOWN_lt_21 = """<h2>an example docstring</h2>
<ul>
<li>list</li>
<li>list</li>
</ul>
<h3>another header</h3>
<pre><code>code block
</code></pre>
<p>indented</p>
<h2 id="hash_style_header">hash style header</h2>"""

MARKED_DOWN_gte_21 = """<h2 id="an-example-docstring">an example docstring</h2>
<ul>
<li>list</li>
<li>list</li>
</ul>
<h3 id="another-header">another header</h3>
<pre><code>code block
</code></pre>
<p>indented</p>
<h2 id="hash-style-header">hash style header</h2>"""


# test strings snatched from http://www.columbia.edu/~fdc/utf8/,
# http://winrus.com/utf8-jap.htm and memory
UTF8_TEST_DOCSTRING = (
    'zażółć gęślą jaźń'
    'Sîne klâwen durh die wolken sint geslagen'
    'Τη γλώσσα μου έδωσαν ελληνική'
    'யாமறிந்த மொழிகளிலே தமிழ்மொழி'
    'На берегу пустынных волн'
    'てすと'
    'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃ'
)


# Apparently there is an issue where docstrings of imported view classes
# do not retain their encoding information even if a module has a proper
# encoding declaration at the top of its source file. Therefore for tests
# to catch unicode related errors, a mock view has to be declared in a separate
# module.
class ViewWithNonASCIICharactersInDocstring(APIView):
    __doc__ = UTF8_TEST_DOCSTRING


class TestViewNamesAndDescriptions(TestCase):
    def test_view_name_uses_class_name(self):
        """
        Ensure view names are based on the class name.
        """
        class MockView(APIView):
            pass
        self.assertEqual(get_view_name(MockView), 'Mock')

    def test_view_description_uses_docstring(self):
        """Ensure view descriptions are based on the docstring."""
        class MockView(APIView):
            """an example docstring
            ====================

            * list
            * list

            another header
            --------------

                code block

            indented

            # hash style header #"""

        self.assertEqual(get_view_description(MockView), DESCRIPTION)

    def test_view_description_supports_unicode(self):
        """
        Unicode in docstrings should be respected.
        """

        self.assertEqual(
            get_view_description(ViewWithNonASCIICharactersInDocstring),
            smart_text(UTF8_TEST_DOCSTRING)
        )

    def test_view_description_can_be_empty(self):
        """
        Ensure that if a view has no docstring,
        then it's description is the empty string.
        """
        class MockView(APIView):
            pass
        self.assertEqual(get_view_description(MockView), '')

    def test_markdown(self):
        """
        Ensure markdown to HTML works as expected.
        """
        if apply_markdown:
            gte_21_match = apply_markdown(DESCRIPTION) == MARKED_DOWN_gte_21
            lt_21_match = apply_markdown(DESCRIPTION) == MARKED_DOWN_lt_21
            self.assertTrue(gte_21_match or lt_21_match)
