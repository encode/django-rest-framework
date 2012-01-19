"""
Get a descriptive name and description for a view.
"""
import re
from djangorestframework.resources import Resource, FormResource, ModelResource


# These a a bit Grungy, but they do the job.

def get_name(view):
    """
    Return a name for the view.

    If view has a name attribute, use that, otherwise use the view's class name, with 'CamelCaseNames' converted to 'Camel Case Names'.
    """

    # If we're looking up the name of a view callable, as found by reverse,
    # grok the class instance that we stored when as_view was called.
    if getattr(view, 'cls_instance', None):
        view = view.cls_instance

    # If this view provides a get_name method, try to use that:
    if callable(getattr(view, 'get_name', None)):
        name = view.get_name()

    # Otherwise if it's a function view use the function's name
    elif getattr(view, '__name__', None) is not None:
        name = view.__name__

    # I ain't got nuthin fo' ya
    else:
        return ''

    return re.sub('(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', ' \\1', name).strip()



def get_description(view):
    """
    Provide a description for the view.

    By default this is the view's docstring with nice unindention applied.
    """

    # If we're looking up the name of a view callable, as found by reverse,
    # grok the class instance that we stored when as_view was called.
    if getattr(view, 'cls_instance', None):
        view = view.cls_instance

    # If this view provides a get_description method, try to use that:
    if callable(getattr(view, 'get_description', None)):
        doc = view.get_description()

    # Otherwise use the view doctring
    elif getattr(view, '__doc__', None):
        doc = view.__doc__

    # I ain't got nuthin fo' ya
    else:
        return ''

    if not doc:
        return ''

    whitespace_counts = [len(line) - len(line.lstrip(' ')) for line in doc.splitlines()[1:] if line.lstrip()]

    # unindent the docstring if needed
    if whitespace_counts:
        whitespace_pattern = '^' + (' ' * min(whitespace_counts))
        return re.sub(re.compile(whitespace_pattern, re.MULTILINE), '', doc)

    # otherwise return it as-is
    return doc

