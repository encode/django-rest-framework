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

    # If this view has a resource that's been overridden, then use that resource for the name
    if getattr(view, 'resource', None) not in (None, Resource, FormResource, ModelResource):
        name = view.resource.__name__
        
        # Chomp of any non-descriptive trailing part of the resource class name
        if name.endswith('Resource') and name != 'Resource':
            name = name[:-len('Resource')]

        # If the view has a descriptive suffix, eg '*** List', '*** Instance'
        if getattr(view, '_suffix', None):
            name += view._suffix
 
    # Otherwise if it's a function view use the function's name
    elif getattr(view, '__name__', None) is not None:
        name = view.__name__

    # If it's a view class with no resource then grok the name from the class name
    elif getattr(view, '__class__', None) is not None:
        name = view.__class__.__name__

        # Chomp of any non-descriptive trailing part of the view class name
        if name.endswith('View') and name != 'View':
            name = name[:-len('View')]

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
        

    # If this view has a resource that's been overridden, then use the resource's doctring
    if getattr(view, 'resource', None) not in (None, Resource, FormResource, ModelResource):
        doc = view.resource.__doc__
    
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
    
