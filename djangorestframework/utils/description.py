"""Get a descriptive name and description for a view,
based on class name and docstring, and override-able by 'name' and 'description' attributes"""
import re

def get_name(view):
    """Return a name for the view.
    
    If view has a name attribute, use that, otherwise use the view's class name, with 'CamelCaseNames' converted to 'Camel Case Names'."""
    if getattr(view, 'name', None) is not None:
        return view.name

    if getattr(view, '__name__', None) is not None:
        name = view.__name__
    elif getattr(view, '__class__', None) is not None:  # TODO: should be able to get rid of this case once refactoring to 1.3 class views is complete
        name = view.__class__.__name__
    else:
        return ''

    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', name).strip()

def get_description(view):
    """Provide a description for the view.

    By default this is the view's docstring with nice unindention applied."""
    if getattr(view, 'description', None) is not None:
        return getattr(view, 'description')

    if getattr(view, '__doc__', None) is not None:
        whitespace_counts = [len(line) - len(line.lstrip(' ')) for line in view.__doc__.splitlines()[1:] if line.lstrip()]

        if whitespace_counts:
            whitespace_pattern = '^' + (' ' * min(whitespace_counts))
            return re.sub(re.compile(whitespace_pattern, re.MULTILINE), '', view.__doc__)

        return view.__doc__
    
    return ''