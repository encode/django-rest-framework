# -- coding: utf-8 --

from __future__ import unicode_literals

from django.test import TestCase
from django.utils.encoding import python_2_unicode_compatible

from rest_framework.compat import apply_markdown
from rest_framework.utils.formatting import dedent
from rest_framework.views import APIView


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


class TestViewNamesAndDescriptions(TestCase):
    def test_view_name_uses_class_name(self):
        """
        Ensure view names are based on the class name.
        """
        class MockView(APIView):
            pass
        assert MockView().get_view_name() == 'Mock'

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

        assert MockView().get_view_description() == DESCRIPTION

    def test_view_description_can_be_empty(self):
        """
        Ensure that if a view has no docstring,
        then it's description is the empty string.
        """
        class MockView(APIView):
            pass
        assert MockView().get_view_description() == ''

    def test_view_description_can_be_promise(self):
        """
        Ensure a view may have a docstring that is actually a lazily evaluated
        class that can be converted to a string.

        See: https://github.com/tomchristie/django-rest-framework/issues/1708
        """
        # use a mock object instead of gettext_lazy to ensure that we can't end
        # up with a test case string in our l10n catalog
        @python_2_unicode_compatible
        class MockLazyStr(object):
            def __init__(self, string):
                self.s = string

            def __str__(self):
                return self.s

        class MockView(APIView):
            __doc__ = MockLazyStr("a gettext string")

        assert MockView().get_view_description() == 'a gettext string'

    def test_markdown(self):
        """
        Ensure markdown to HTML works as expected.
        """
        if apply_markdown:
            gte_21_match = apply_markdown(DESCRIPTION) == MARKED_DOWN_gte_21
            lt_21_match = apply_markdown(DESCRIPTION) == MARKED_DOWN_lt_21
            assert gte_21_match or lt_21_match


def test_dedent_tabs():
    result = 'first string\n\nsecond string'
    assert dedent("    first string\n\n    second string") == result
    assert dedent("first string\n\n    second string") == result
    assert dedent("\tfirst string\n\n\tsecond string") == result
    assert dedent("first string\n\n\tsecond string") == result
