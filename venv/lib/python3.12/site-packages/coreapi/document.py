# coding: utf-8
from __future__ import unicode_literals
from collections import OrderedDict, namedtuple
from coreapi.compat import string_types
import itypes


def _to_immutable(value):
    if isinstance(value, dict):
        return Object(value)
    elif isinstance(value, list):
        return Array(value)
    return value


def _repr(node):
    from coreapi.codecs.python import PythonCodec
    return PythonCodec().encode(node)


def _str(node):
    from coreapi.codecs.display import DisplayCodec
    return DisplayCodec().encode(node)


def _key_sorting(item):
    """
    Document and Object sorting.
    Regular attributes sorted alphabetically.
    Links are sorted based on their URL and action.
    """
    key, value = item
    if isinstance(value, Link):
        action_priority = {
            'get': 0,
            'post': 1,
            'put': 2,
            'patch': 3,
            'delete': 4
        }.get(value.action, 5)
        return (1, (value.url, action_priority))
    return (0, key)


# The field class, as used by Link objects:

# NOTE: 'type', 'description' and 'example' are now deprecated,
#       in favor of 'schema'.
Field = namedtuple('Field', ['name', 'required', 'location', 'schema', 'description', 'type', 'example'])
Field.__new__.__defaults__ = (False, '', None, None, None, None)


# The Core API primitives:

class Document(itypes.Dict):
    """
    The Core API document type.

    Expresses the data that the client may access,
    and the actions that the client may perform.
    """
    def __init__(self, url=None, title=None, description=None, media_type=None, content=None):
        content = {} if (content is None) else content

        if url is not None and not isinstance(url, string_types):
            raise TypeError("'url' must be a string.")
        if title is not None and not isinstance(title, string_types):
            raise TypeError("'title' must be a string.")
        if description is not None and not isinstance(description, string_types):
            raise TypeError("'description' must be a string.")
        if media_type is not None and not isinstance(media_type, string_types):
            raise TypeError("'media_type' must be a string.")
        if not isinstance(content, dict):
            raise TypeError("'content' must be a dict.")
        if any([not isinstance(key, string_types) for key in content.keys()]):
            raise TypeError('content keys must be strings.')

        self._url = '' if (url is None) else url
        self._title = '' if (title is None) else title
        self._description = '' if (description is None) else description
        self._media_type = '' if (media_type is None) else media_type
        self._data = {key: _to_immutable(value) for key, value in content.items()}

    def clone(self, data):
        return self.__class__(self.url, self.title, self.description, self.media_type, data)

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)

    def __eq__(self, other):
        if self.__class__ == other.__class__:
            return (
                self.url == other.url and
                self.title == other.title and
                self._data == other._data
            )
        return super(Document, self).__eq__(other)

    @property
    def url(self):
        return self._url

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def media_type(self):
        return self._media_type

    @property
    def data(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if not isinstance(value, Link)
        ])

    @property
    def links(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if isinstance(value, Link)
        ])


class Object(itypes.Dict):
    """
    An immutable mapping of strings to values.
    """
    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        if any([not isinstance(key, string_types) for key in data.keys()]):
            raise TypeError('Object keys must be strings.')
        self._data = {key: _to_immutable(value) for key, value in data.items()}

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)

    @property
    def data(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if not isinstance(value, Link)
        ])

    @property
    def links(self):
        return OrderedDict([
            (key, value) for key, value in self.items()
            if isinstance(value, Link)
        ])


class Array(itypes.List):
    """
    An immutable list type container.
    """
    def __init__(self, *args):
        self._data = [_to_immutable(value) for value in list(*args)]

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)


class Link(itypes.Object):
    """
    Links represent the actions that a client may perform.
    """
    def __init__(self, url=None, action=None, encoding=None, transform=None, title=None, description=None, fields=None):
        if (url is not None) and (not isinstance(url, string_types)):
            raise TypeError("Argument 'url' must be a string.")
        if (action is not None) and (not isinstance(action, string_types)):
            raise TypeError("Argument 'action' must be a string.")
        if (encoding is not None) and (not isinstance(encoding, string_types)):
            raise TypeError("Argument 'encoding' must be a string.")
        if (transform is not None) and (not isinstance(transform, string_types)):
            raise TypeError("Argument 'transform' must be a string.")
        if (title is not None) and (not isinstance(title, string_types)):
            raise TypeError("Argument 'title' must be a string.")
        if (description is not None) and (not isinstance(description, string_types)):
            raise TypeError("Argument 'description' must be a string.")
        if (fields is not None) and (not isinstance(fields, (list, tuple))):
            raise TypeError("Argument 'fields' must be a list.")
        if (fields is not None) and any([
            not (isinstance(item, string_types) or isinstance(item, Field))
            for item in fields
        ]):
            raise TypeError("Argument 'fields' must be a list of strings or fields.")

        self._url = '' if (url is None) else url
        self._action = '' if (action is None) else action
        self._encoding = '' if (encoding is None) else encoding
        self._transform = '' if (transform is None) else transform
        self._title = '' if (title is None) else title
        self._description = '' if (description is None) else description
        self._fields = () if (fields is None) else tuple([
            item if isinstance(item, Field) else Field(item, required=False, location='')
            for item in fields
        ])

    @property
    def url(self):
        return self._url

    @property
    def action(self):
        return self._action

    @property
    def encoding(self):
        return self._encoding

    @property
    def transform(self):
        return self._transform

    @property
    def title(self):
        return self._title

    @property
    def description(self):
        return self._description

    @property
    def fields(self):
        return self._fields

    def __eq__(self, other):
        return (
            isinstance(other, Link) and
            self.url == other.url and
            self.action == other.action and
            self.encoding == other.encoding and
            self.transform == other.transform and
            self.description == other.description and
            sorted(self.fields, key=lambda f: f.name) == sorted(other.fields, key=lambda f: f.name)
        )

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)


class Error(itypes.Dict):
    def __init__(self, title=None, content=None):
        data = {} if (content is None) else content

        if title is not None and not isinstance(title, string_types):
            raise TypeError("'title' must be a string.")
        if content is not None and not isinstance(content, dict):
            raise TypeError("'content' must be a dict.")
        if any([not isinstance(key, string_types) for key in data.keys()]):
            raise TypeError('content keys must be strings.')

        self._title = '' if (title is None) else title
        self._data = {key: _to_immutable(value) for key, value in data.items()}

    def __iter__(self):
        items = sorted(self._data.items(), key=_key_sorting)
        return iter([key for key, value in items])

    def __repr__(self):
        return _repr(self)

    def __str__(self):
        return _str(self)

    def __eq__(self, other):
        return (
            isinstance(other, Error) and
            self.title == other.title and
            self._data == other._data
        )

    @property
    def title(self):
        return self._title

    def get_messages(self):
        messages = []
        for value in self.values():
            if isinstance(value, Array):
                messages += [
                    item for item in value if isinstance(item, string_types)
                ]
        return messages
