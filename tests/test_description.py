import pytest
from django.test import TestCase

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

# hash style header #

```json
[{
    "alpha": 1,
    "beta": "this is a string"
}]
```"""


# If markdown is installed we also test it's working
# (and that our wrapped forces '=' to h2 and '-' to h3)
MARKDOWN_DOCSTRING = """<h2 id="an-example-docstring">an example docstring</h2>
<ul>
<li>list</li>
<li>list</li>
</ul>
<h3 id="another-header">another header</h3>
<pre><code>code block
</code></pre>
<p>indented</p>
<h2 id="hash-style-header">hash style header</h2>
<div class="highlight"><pre><span></span><span class="p">[{</span><br /><span class="w">    </span><span class="nt">&quot;alpha&quot;</span><span class="p">:</span><span class="w"> </span><span class="mi">1</span><span class="p">,</span><br /><span class="w">    </span><span class="nt">&quot;beta&quot;</span><span class="p">:</span><span class="w"> </span><span class="s2">&quot;this is a string&quot;</span><br /><span class="p">}]</span><br /></pre></div>
<p><br /></p>"""


class TestViewNamesAndDescriptions(TestCase):
    def test_view_name_uses_class_name(self):
        """
        Ensure view names are based on the class name.
        """
        class MockView(APIView):
            pass
        assert MockView().get_view_name() == 'Mock'

    def test_view_name_uses_name_attribute(self):
        class MockView(APIView):
            name = 'Foo'
        assert MockView().get_view_name() == 'Foo'

    def test_view_name_uses_suffix_attribute(self):
        class MockView(APIView):
            suffix = 'List'
        assert MockView().get_view_name() == 'Mock List'

    def test_view_name_preferences_name_over_suffix(self):
        class MockView(APIView):
            name = 'Foo'
            suffix = 'List'
        assert MockView().get_view_name() == 'Foo'

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

            # hash style header #

            ```json
            [{
                "alpha": 1,
                "beta": "this is a string"
            }]
            ```"""

        assert MockView().get_view_description() == DESCRIPTION

    def test_view_description_uses_description_attribute(self):
        class MockView(APIView):
            description = 'Foo'
        assert MockView().get_view_description() == 'Foo'

    def test_view_description_allows_empty_description(self):
        class MockView(APIView):
            """Description."""
            description = ''
        assert MockView().get_view_description() == ''

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

        See: https://github.com/encode/django-rest-framework/issues/1708
        """
        # use a mock object instead of gettext_lazy to ensure that we can't end
        # up with a test case string in our l10n catalog

        class MockLazyStr:
            def __init__(self, string):
                self.s = string

            def __str__(self):
                return self.s

        class MockView(APIView):
            __doc__ = MockLazyStr("a gettext string")

        assert MockView().get_view_description() == 'a gettext string'

    @pytest.mark.skipif(not apply_markdown, reason="Markdown is not installed")
    def test_markdown(self):
        """
        Ensure markdown to HTML works as expected.
        """
        assert apply_markdown(DESCRIPTION) == MARKDOWN_DOCSTRING


def test_dedent_tabs():
    result = 'first string\n\nsecond string'
    assert dedent("    first string\n\n    second string") == result
    assert dedent("first string\n\n    second string") == result
    assert dedent("\tfirst string\n\n\tsecond string") == result
    assert dedent("first string\n\n\tsecond string") == result
