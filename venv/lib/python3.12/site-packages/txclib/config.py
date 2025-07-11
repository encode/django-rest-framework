try:
    import configparser
except ImportError:
    import ConfigParser as configparser

import six

from txclib.exceptions import MalformedConfigFile


class OrderedRawConfigParser(configparser.RawConfigParser):
    """
    Overload standard Class ConfigParser.RawConfigParser
    """
    def write(self, fp):
        """Write an .ini-format representation of the configuration state."""
        if self._defaults:
            fp.write("[%s]\n" % DEFAULTSECT)
            for key in sorted(self._defaults):
                fp.write("%s = %s\n" % (key, str(self._defaults[key]).
                         replace('\n', '\n\t')))
            fp.write("\n")
        for section in self._sections:
            fp.write("[%s]\n" % section)
            for key in sorted(self._sections[section]):
                if key != "__name__":
                    fp.write("%s = %s\n" %
                             (key, str(self._sections[section][key]).
                              replace('\n', '\n\t')))
            fp.write("\n")

    optionxform = str


_NOTFOUND = object()


class Flipdict(dict):
    """An injective (one-to-one) python dict.  Ensures that each key maps
    to a unique value, and each value maps back to that same key.

    Code mostly taken from here:
    http://code.activestate.com/recipes/576968-flipdict-python-dict-that-also-maintains-a-one-to-/
    """

    def __init__(self, *args, **kw):
        self._flip = dict.__new__(self.__class__)
        setattr(self._flip, "_flip", self)
        for key, val in six.iteritems(dict(*args, **kw)):
            self[key] = val

    @property
    def flip(self):
        """The inverse mapping."""
        return self._flip

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, dict(self))

    __str__ = __repr__

    def copy(self):
        return self.__class__(self)

    @classmethod
    def fromkeys(cls, keys, value=None):
        return cls(dict.fromkeys(keys, value))

    def __setitem__(self, key, val):
        k = self._flip.get(val, _NOTFOUND)
        if not (k is _NOTFOUND or k == key):
            raise MalformedConfigFile("Your lang map configuration is not correct. "
                                      "Duplicate entry detected with value '%s'. "
                                      "Keys and values should be unique." % val)

        v = self.get(key, _NOTFOUND)
        if v is not _NOTFOUND:
            dict.__delitem__(self._flip, v)

        dict.__setitem__(self,       key, val)
        dict.__setitem__(self._flip, val, key)

    def setdefault(self, key, default=None):
        # Copied from python's UserDict.DictMixin code.
        try:
            return self[key]
        except KeyError:
            self[key] = default
            return default

    def update(self, other=None, **kwargs):
        # Copied from python's UserDict.DictMixin code.
        # Make progressively weaker assumptions about "other"
        if other is None:
            pass
        elif hasattr(other, 'items'):
            for k, v in six.iteritems(other):
                self[k] = v
        elif hasattr(other, 'keys'):
            for k in list(other.keys()):
                self[k] = other[k]
        else:
            for k, v in other:
                self[k] = v
        if kwargs:
            self.update(kwargs)

    def __delitem__(self, key):
        val = dict.pop(self, key)
        dict.__delitem__(self._flip, val)

    def pop(self, key, *args):
        val = dict.pop(self, key, *args)
        dict.__delitem__(self._flip, val)
        return val

    def popitem(self):
        key, val = dict.popitem(self)
        dict.__delitem__(self._flip, val)
        return key, val

    def clear(self):
        dict.clear(self)
        dict.clear(self._flip)


import os
import ssl

CERT_REQUIRED = getattr(ssl, os.environ.get('TX_CERT_MODE', 'CERT_REQUIRED'))
