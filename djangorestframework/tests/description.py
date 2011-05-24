from django.test import TestCase
from djangorestframework.views import View
from djangorestframework.compat import apply_markdown
from djangorestframework.utils.description import get_name, get_description

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

# If markdown is installed we also test it's working (and that our wrapped forces '=' to h2 and '-' to h3)
MARKED_DOWN = """<h2>an example docstring</h2>
<ul>
<li>list</li>
<li>list</li>
</ul>
<h3>another header</h3>
<pre><code>code block
</code></pre>
<p>indented</p>
<h2 id="hash_style_header">hash style header</h2>"""


class TestViewNamesAndDescriptions(TestCase):
    def test_resource_name_uses_classname_by_default(self):
        """Ensure Resource names are based on the classname by default."""
        class MockView(View):
            pass
        self.assertEquals(get_name(MockView()), 'Mock')

    # This has been turned off now.
    #def test_resource_name_can_be_set_explicitly(self):
    #    """Ensure Resource names can be set using the 'name' class attribute."""
    #    example = 'Some Other Name'
    #    class MockView(View):
    #        name = example
    #    self.assertEquals(get_name(MockView()), example)

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
        
        self.assertEquals(get_description(MockView()), DESCRIPTION)

    # This has been turned off now
    #def test_resource_description_can_be_set_explicitly(self):
    #    """Ensure Resource descriptions can be set using the 'description' class attribute."""
    #    example = 'Some other description'
    #    class MockView(View):
    #        """docstring"""
    #        description = example
    #    self.assertEquals(get_description(MockView()), example)
 
    #def test_resource_description_does_not_require_docstring(self):
    #    """Ensure that empty docstrings do not affect the Resource's description if it has been set using the 'description' class attribute."""
    #    example = 'Some other description'
    #    class MockView(View):
    #        description = example
    #    self.assertEquals(get_description(MockView()), example)

    def test_resource_description_can_be_empty(self):
        """Ensure that if a resource has no doctring or 'description' class attribute, then it's description is the empty string"""
        class MockView(View):
            pass
        self.assertEquals(get_description(MockView()), '')
  
    def test_markdown(self):
        """Ensure markdown to HTML works as expected"""
        if apply_markdown:
            self.assertEquals(apply_markdown(DESCRIPTION), MARKED_DOWN)
