from contextlib import contextmanager
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import NoReverseMatch
from django.utils import six
from rest_framework.settings import api_settings


@contextmanager
def temporary_setting(setting, value, module=None):
    """
    Temporarily change value of setting for test.

    Optionally reload given module, useful when module uses value of setting on
    import.
    """
    original_value = getattr(api_settings, setting)
    setattr(api_settings, setting, value)

    if module is not None:
        six.moves.reload_module(module)

    yield

    setattr(api_settings, setting, original_value)

    if module is not None:
        six.moves.reload_module(module)


class MockObject(object):
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


class MockQueryset(object):
    def __init__(self, iterable):
        self.items = iterable

    def get(self, **lookup):
        for item in self.items:
            if all([
                getattr(item, key, None) == value
                for key, value in lookup.items()
            ]):
                return item
        raise ObjectDoesNotExist()


class BadType(object):
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
