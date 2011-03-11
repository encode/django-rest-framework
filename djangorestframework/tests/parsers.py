"""
..
    >>> from djangorestframework.parsers import FormParser
    >>> from djangorestframework.resource import Resource
    >>> from djangorestframework.compat import RequestFactory
    >>> from urllib import urlencode
    >>> req = RequestFactory().get('/')
    >>> some_resource = Resource()
    >>> trash = some_resource.dispatch(req)# Some variables are set only when calling dispatch

Data flatening
----------------

Here is some example data, which would eventually be sent along with a post request :

    >>> inpt = urlencode([
    ...     ('key1', 'bla1'),
    ...     ('key2', 'blo1'), ('key2', 'blo2'),
    ... ])

Default behaviour for :class:`parsers.FormParser`, is to return a single value for each parameter :

    >>> FormParser(some_resource).parse(inpt) == {'key1': 'bla1', 'key2': 'blo1'}
    True

However, you can customize this behaviour by subclassing :class:`parsers.FormParser`, and overriding :meth:`parsers.FormParser.is_a_list` :

    >>> class MyFormParser(FormParser):
    ... 
    ...     def is_a_list(self, key, val_list):
    ...         return len(val_list) > 1

This new parser only flattens the lists of parameters that contain a single value.

    >>> MyFormParser(some_resource).parse(inpt) == {'key1': 'bla1', 'key2': ['blo1', 'blo2']}
    True

Submitting an empty list
--------------------------

When submitting an empty select multiple, like this one ::

    <select multiple="multiple" name="key2"></select>

The browsers usually strip the parameter completely. A hack to avoid this, and therefore being able to submit an empty select multiple, is to submit a value that tells the server that the list is empty ::

    <select multiple="multiple" name="key2"><option value="_empty"></select>

:class:`parsers.FormParser` provides the server-side implementation for this hack. Considering the following posted data :

    >>> inpt = urlencode([
    ...     ('key1', 'blo1'), ('key1', '_empty'),
    ...     ('key2', '_empty'),
    ... ])

:class:`parsers.FormParser` strips the values ``_empty`` from all the lists.

    >>> MyFormParser(some_resource).parse(inpt) == {'key1': 'blo1'}
    True

Oh ... but wait a second, the parameter ``key2`` isn't even supposed to be a list, so the parser just stripped it.

    >>> class MyFormParser(FormParser):
    ... 
    ...     def is_a_list(self, key, val_list):
    ...         return key == 'key2'
    ... 
    >>> MyFormParser(some_resource).parse(inpt) == {'key1': 'blo1', 'key2': []}
    True

Better like that. Note also that you can configure something else than ``_empty`` for the empty value by setting :class:`parsers.FormParser.EMPTY_VALUE`.
"""
