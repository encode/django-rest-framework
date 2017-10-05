"""
utils.py        # Shared helper functions

See schemas.__init__.py for package overview.
"""
from rest_framework.mixins import RetrieveModelMixin


def is_list_view(path, method, view):
    """
    Return True if the given path/method appears to represent a list view.
    """
    if hasattr(view, 'action'):
        # Viewsets have an explicitly defined action, which we can inspect.
        return view.action == 'list'

    if method.lower() != 'get':
        return False
    if isinstance(view, RetrieveModelMixin):
        return False
    path_components = path.strip('/').split('/')
    if path_components and '{' in path_components[-1]:
        return False
    return True
