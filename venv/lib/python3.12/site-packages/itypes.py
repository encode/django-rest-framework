# coding: utf-8
try:
    from collections.abc import Mapping, Sequence
except ImportError:  # support for python 2.x
    from collections import Mapping, Sequence


__version__ = '1.2.0'


def to_mutable(instance):
    if isinstance(instance, Dict):
        return {
            key: to_mutable(value)
            for key, value in instance.items()
        }
    elif isinstance(instance, List):
        return [
            to_mutable(value)
            for value in instance
        ]
    return instance


def to_immutable(value):
    if isinstance(value, dict):
        return Dict(value)
    elif isinstance(value, list):
        return List(value)
    return value


def _to_hashable(instance):
    if isinstance(instance, Dict):
        items = sorted(instance.items(), key=lambda item: item[0])
        return (
            (key, _to_hashable(value))
            for key, value in items
        )
    elif isinstance(instance, List):
        return [
            _to_hashable(value)
            for value in instance
        ]
    return instance


def _set_in(node, keys, value):
    if not keys:
        return value
    elif len(keys) == 1:
        return node.set(keys[0], value)

    key = keys[0]
    child = node[key]
    if not isinstance(child, (Dict, List)):
        msg = "Expected a container type at key '%s', but got '%s'"
        raise KeyError(msg % type(child))
    child = child.set_in(keys[1:], value)
    return node.set(key, child)


def _delete_in(node, keys):
    if not keys:
        return
    elif len(keys) == 1:
        return node.delete(keys[0])

    key = keys[0]
    child = node[key]
    if not isinstance(child, (Dict, List)):
        msg = "Expected a container type at key '%s', but got '%s'"
        raise KeyError(msg % type(child))
    child = child.delete_in(keys[1:])
    return node.set(key, child)


def _get_in(node, keys, default=None):
    if not keys:
        return default

    key = keys[0]
    try:
        child = node[key]
    except (KeyError, IndexError):
        return default

    if len(keys) == 1:
        return child
    return child.get_in(keys[1:], default=default)


class Object(object):
    def __setattr__(self, key, value):
        if key.startswith('_'):
            return object.__setattr__(self, key, value)
        msg = "'%s' object doesn't support property assignment."
        raise TypeError(msg % self.__class__.__name__)


class Dict(Mapping):
    def __init__(self, *args, **kwargs):
        self._data = {
            key: to_immutable(value)
            for key, value in dict(*args, **kwargs).items()
        }

    def __setattr__(self, key, value):
        if key.startswith('_'):
            return object.__setattr__(self, key, value)
        msg = "'%s' object doesn't support property assignment."
        raise TypeError(msg % self.__class__.__name__)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._data == other._data
        return self._data == other

    def __hash__(self):
        return hash(_to_hashable(self))

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            to_mutable(self)
        )

    def __str__(self):
        return str(self._data)

    def set(self, key, value):
        data = dict(self._data)
        data[key] = value
        if hasattr(self, 'clone'):
            return self.clone(data)
        return type(self)(data)

    def delete(self, key):
        data = dict(self._data)
        data.pop(key)
        if hasattr(self, 'clone'):
            return self.clone(data)
        return type(self)(data)

    def get_in(self, keys, default=None):
        return _get_in(self, keys, default=default)

    def set_in(self, keys, value):
        return _set_in(self, keys, value)

    def delete_in(self, keys):
        return _delete_in(self, keys)


class List(Sequence):
    def __init__(self, *args):
        self._data = [
            to_immutable(value)
            for value in list(*args)
        ]

    def __setattr__(self, key, value):
        if key == '_data':
            return object.__setattr__(self, key, value)
        msg = "'%s' object doesn't support property assignment."
        raise TypeError(msg % self.__class__.__name__)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._data == other._data
        return self._data == other

    def __hash__(self):
        return hash(_to_hashable(self))

    def __repr__(self):
        return "%s(%s)" % (
            self.__class__.__name__,
            to_mutable(self)
        )

    def __str__(self):
        return str(self._data)

    def set(self, key, value):
        data = list(self._data)
        data[key] = value
        if hasattr(self, 'clone'):
            return self.clone(data)
        return type(self)(data)

    def delete(self, key):
        data = list(self._data)
        data.pop(key)
        if hasattr(self, 'clone'):
            return self.clone(data)
        return type(self)(data)

    def get_in(self, keys, default=None):
        return _get_in(self, keys, default=default)

    def set_in(self, keys, value):
        return _set_in(self, keys, value)

    def delete_in(self, keys):
        return _delete_in(self, keys)
