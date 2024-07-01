from operator import attrgetter

from django.core.exceptions import ObjectDoesNotExist
from django.urls import NoReverseMatch


class MockObject:
    def __init__(self, **kwargs):
        self._kwargs = kwargs
        for key, val in kwargs.items():
            setattr(self, key, val)

    def __str__(self):
        kwargs_str = ', '.join([
            '%s=%s' % (key, value)
            for key, value in sorted(self._kwargs.items())
        ])
        return '<MockObject %s>' % kwargs_str


class MockQueryset:
    def __init__(self, iterable):
        self.items = iterable

    def __getitem__(self, val):
        return self.items[val]

    def get(self, **lookup):
        result = self.filter(**lookup).all()
        if len(result) > 0:
            return result[0]
        raise ObjectDoesNotExist()

    def all(self):
        return list(self.items)

    def filter(self, **lookup):
        return MockQueryset([
            item
            for item in self.items
            if all([
                attrgetter(key.replace("__in", "").replace('__', '.'))(item) in value
                if key.endswith("__in")
                else attrgetter(key.replace('__', '.'))(item) == value
                for key, value in lookup.items()
            ])
        ])

    def annotate(self, **kwargs):
        for key, value in kwargs.items():
            for item in self.items:
                setattr(item, key, attrgetter(value.name.replace('__', '.'))(item))
        return self


class BadType:
    """
    When used as a lookup with a `MockQueryset`, these objects
    will raise a `TypeError`, as occurs in Django when making
    queryset lookups with an incorrect type for the lookup value.
    """

    def __eq__(self):
        raise TypeError()


def mock_reverse(view_name, args=None, kwargs=None, request=None, format=None):
    args = args or []
    kwargs = kwargs or {}
    value = (args + list(kwargs.values()) + ['-'])[0]
    prefix = 'http://example.org' if request else ''
    suffix = ('.' + format) if (format is not None) else ''
    return '%s/%s/%s%s/' % (prefix, view_name, value, suffix)


def fail_reverse(view_name, args=None, kwargs=None, request=None, format=None):
    raise NoReverseMatch()
