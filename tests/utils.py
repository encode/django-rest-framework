from operator import attrgetter

from django.core.exceptions import ObjectDoesNotExist
from django.urls import NoReverseMatch


class MockObject:
    """
    A mock object for testing purposes.
    """

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        sorted_kwargs = ', '.join(['%s=%s' % (key, value) for key, value in sorted(self._kwargs.items())])
        return f'<MockObject {sorted_kwargs}>'


class MockQueryset:
    """
    A mock queryset for testing purposes.
    """

    def __init__(self, iterable):
        self.items = iterable

    def __getitem__(self, index):
        return self.items[index]

    def get(self, **lookup):
        for item in self.items:
            if all(attrgetter(key.replace('__', '.'))(item) == value for key, value in lookup.items()):
                return item
        raise ObjectDoesNotExist()


class BadType:
    """
    Raise a `TypeError` when used as a lookup value with a `MockQueryset`.
    This behavior mimics Django's queryset lookups with incorrect types.
    """

    def __eq__(self):
        raise TypeError()


def mock_reverse(view_name, args=None, kwargs=None, request=None, format=None):
    """
    Mocked implementation of Django's reverse function for testing.
    """

    args = args or []
    kwargs = kwargs or {}
    first_value = (args + list(kwargs.values()) + ['-'])[0]
    prefix = 'http://example.org' if request else ''
    suffix = f'.{format}' if format is not None else ''
    return f'{prefix}/{view_name}/{first_value}{suffix}/'


def fail_reverse(view_name, args=None, kwargs=None, request=None, format=None):
    """
    Mocked implementation of Django's reverse function to raise a NoReverseMatch for testing.
    """
    raise NoReverseMatch()
