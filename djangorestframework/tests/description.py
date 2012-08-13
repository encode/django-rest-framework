from django.test import TestCase
from djangorestframework.views import View
from djangorestframework.compat import apply_markdown

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
    def test_resource_name_uses_classname_by_default(self):
        """Ensure Resource names are based on the classname by default."""
        class MockView(View):
            pass
        self.assertEquals(MockView().get_name(), 'Mock')

    def test_resource_name_can_be_set_explicitly(self):
        """Ensure Resource names can be set using the 'get_name' method."""
        example = 'Some Other Name'
        class MockView(View):
            def get_name(self):
                return example
        self.assertEquals(MockView().get_name(), example)

    def test_resource_description_uses_docstring_by_default(self):
        """Ensure Resource names are based on the docstring by default."""
        class MockView(View):
            """an example docstring
            ====================

            * list
            * list

            another header
            --------------

                code block

            indented

            # hash style header #"""

        self.assertEquals(MockView().get_description(), DESCRIPTION)

    def test_resource_description_can_be_set_explicitly(self):
        """Ensure Resource descriptions can be set using the 'get_description' method."""
        example = 'Some other description'
        class MockView(View):
            """docstring"""
            def get_description(self):
                return example
        self.assertEquals(MockView().get_description(), example)

    def test_resource_description_does_not_require_docstring(self):
        """Ensure that empty docstrings do not affect the Resource's description if it has been set using the 'get_description' method."""
        example = 'Some other description'
        class MockView(View):
            def get_description(self):
                return example
        self.assertEquals(MockView().get_description(), example)

    def test_resource_description_can_be_empty(self):
        """Ensure that if a resource has no doctring or 'description' class attribute, then it's description is the empty string."""
        class MockView(View):
            pass
        self.assertEquals(MockView().get_description(), '')

    def test_markdown(self):
        """Ensure markdown to HTML works as expected"""
        if apply_markdown:
            gte_21_match = apply_markdown(DESCRIPTION) == MARKED_DOWN_gte_21
            lt_21_match = apply_markdown(DESCRIPTION) == MARKED_DOWN_lt_21
            self.assertTrue(gte_21_match or lt_21_match)
