"""
The `compat` module provides support for backwards compatibility with older
versions of Django/Python, and compatibility wrappers around optional packages.
"""

# flake8: noqa
from __future__ import unicode_literals

import django
from django.conf import settings
from django.db import connection, transaction
from django.utils import six
from django.views.generic import View

try:
    import importlib  # Available in Python 3.1+
except ImportError:
    from django.utils import importlib  # Will be removed in Django 1.9


def unicode_repr(instance):
    # Get the repr of an instance, but ensure it is a unicode string
    # on both python 3 (already the case) and 2 (not the case).
    if six.PY2:
        return repr(instance).decode('utf-8')
    return repr(instance)


def unicode_to_repr(value):
    # Coerce a unicode string to the correct repr return type, depending on
    # the Python version. We wrap all our `__repr__` implementations with
    # this and then use unicode throughout internally.
    if six.PY2:
        return value.encode('utf-8')
    return value


def unicode_http_header(value):
    # Coerce HTTP header value to unicode.
    if isinstance(value, six.binary_type):
        return value.decode('iso-8859-1')
    return value


def total_seconds(timedelta):
    # TimeDelta.total_seconds() is only available in Python 2.7
    if hasattr(timedelta, 'total_seconds'):
        return timedelta.total_seconds()
    else:
        return (timedelta.days * 86400.0) + float(timedelta.seconds) + (timedelta.microseconds / 1000000.0)


def distinct(queryset, base):
    if settings.DATABASES[queryset.db]["ENGINE"] == "django.db.backends.oracle":
        # distinct analogue for Oracle users
        return base.filter(pk__in=set(queryset.values_list('pk', flat=True)))
    return queryset.distinct()


# OrderedDict only available in Python 2.7.
# This will always be the case in Django 1.7 and above, as these versions
# no longer support Python 2.6.
# For Django <= 1.6 and Python 2.6 fall back to SortedDict.
try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict


# contrib.postgres only supported from 1.8 onwards.
try:
    from django.contrib.postgres import fields as postgres_fields
except ImportError:
    postgres_fields = None


# django-filter is optional
try:
    import django_filters
except ImportError:
    django_filters = None

if django.VERSION >= (1, 6):
    def clean_manytomany_helptext(text):
        return text
else:
    # Up to version 1.5 many to many fields automatically suffix
    # the `help_text` attribute with hardcoded text.
    def clean_manytomany_helptext(text):
        if text.endswith(' Hold down "Control", or "Command" on a Mac, to select more than one.'):
            text = text[:-69]
        return text

# Django-guardian is optional. Import only if guardian is in INSTALLED_APPS
# Fixes (#1712). We keep the try/except for the test suite.
guardian = None
if 'guardian' in settings.INSTALLED_APPS:
    try:
        import guardian
        import guardian.shortcuts  # Fixes #1624
    except ImportError:
        pass


def get_model_name(model_cls):
    try:
        return model_cls._meta.model_name
    except AttributeError:
        # < 1.6 used module_name instead of model_name
        return model_cls._meta.module_name


# MinValueValidator, MaxValueValidator et al. only accept `message` in 1.8+
if django.VERSION >= (1, 8):
    from django.core.validators import MinValueValidator, MaxValueValidator
    from django.core.validators import MinLengthValidator, MaxLengthValidator
else:
    from django.core.validators import MinValueValidator as DjangoMinValueValidator
    from django.core.validators import MaxValueValidator as DjangoMaxValueValidator
    from django.core.validators import MinLengthValidator as DjangoMinLengthValidator
    from django.core.validators import MaxLengthValidator as DjangoMaxLengthValidator


    class MinValueValidator(DjangoMinValueValidator):
        def __init__(self, *args, **kwargs):
            self.message = kwargs.pop('message', self.message)
            super(MinValueValidator, self).__init__(*args, **kwargs)


    class MaxValueValidator(DjangoMaxValueValidator):
        def __init__(self, *args, **kwargs):
            self.message = kwargs.pop('message', self.message)
            super(MaxValueValidator, self).__init__(*args, **kwargs)


    class MinLengthValidator(DjangoMinLengthValidator):
        def __init__(self, *args, **kwargs):
            self.message = kwargs.pop('message', self.message)
            super(MinLengthValidator, self).__init__(*args, **kwargs)


    class MaxLengthValidator(DjangoMaxLengthValidator):
        def __init__(self, *args, **kwargs):
            self.message = kwargs.pop('message', self.message)
            super(MaxLengthValidator, self).__init__(*args, **kwargs)


# URLValidator only accepts `message` in 1.6+
if django.VERSION >= (1, 6):
    from django.core.validators import URLValidator
else:
    from django.core.validators import URLValidator as DjangoURLValidator


    class URLValidator(DjangoURLValidator):
        def __init__(self, *args, **kwargs):
            self.message = kwargs.pop('message', self.message)
            super(URLValidator, self).__init__(*args, **kwargs)


# EmailValidator requires explicit regex prior to 1.6+
if django.VERSION >= (1, 6):
    from django.core.validators import EmailValidator
else:
    from django.core.validators import EmailValidator as DjangoEmailValidator
    from django.core.validators import email_re


    class EmailValidator(DjangoEmailValidator):
        def __init__(self, *args, **kwargs):
            super(EmailValidator, self).__init__(email_re, *args, **kwargs)


# PATCH method is not implemented by Django
if 'patch' not in View.http_method_names:
    View.http_method_names = View.http_method_names + ['patch']

try:
    from django.functional import lru_cache
except ImportError:
    from collections import namedtuple
    from functools import update_wrapper
    from threading import RLock

    _CacheInfo = namedtuple("CacheInfo", ["hits", "misses", "maxsize", "currsize"])

    class _HashedSeq(list):
        __slots__ = 'hashvalue'

        def __init__(self, tup, hash=hash):
            self[:] = tup
            self.hashvalue = hash(tup)

        def __hash__(self):
            return self.hashvalue

    def _make_key(args, kwds, typed,
                 kwd_mark = (object(),),
                 fasttypes = set((int, str, frozenset, type(None))),
                 sorted=sorted, tuple=tuple, type=type, len=len):
        """Make a cache key from optionally typed positional and keyword arguments"""
        key = args
        if kwds:
            sorted_items = sorted(kwds.items())
            key += kwd_mark
            for item in sorted_items:
                key += item
        if typed:
            key += tuple(type(v) for v in args)
            if kwds:
                key += tuple(type(v) for k, v in sorted_items)
        elif len(key) == 1 and type(key[0]) in fasttypes:
            return key[0]
        return _HashedSeq(key)

    def lru_cache(maxsize=100, typed=False):
        """Least-recently-used cache decorator.

        If *maxsize* is set to None, the LRU features are disabled and the cache
        can grow without bound.

        If *typed* is True, arguments of different types will be cached separately.
        For example, f(3.0) and f(3) will be treated as distinct calls with
        distinct results.

        Arguments to the cached function must be hashable.

        View the cache statistics named tuple (hits, misses, maxsize, currsize) with
        f.cache_info().  Clear the cache and statistics with f.cache_clear().
        Access the underlying function with f.__wrapped__.

        See:  https://en.wikipedia.org/wiki/Cache_algorithms#Least_Recently_Used

        """

        # Users should only access the lru_cache through its public API:
        #       cache_info, cache_clear, and f.__wrapped__
        # The internals of the lru_cache are encapsulated for thread safety and
        # to allow the implementation to change (including a possible C version).

        def decorating_function(user_function):

            cache = dict()
            stats = [0, 0]                  # make statistics updateable non-locally
            HITS, MISSES = 0, 1             # names for the stats fields
            make_key = _make_key
            cache_get = cache.get           # bound method to lookup key or return None
            _len = len                      # localize the global len() function
            lock = RLock()                  # because linkedlist updates aren't threadsafe
            root = []                       # root of the circular doubly linked list
            root[:] = [root, root, None, None]      # initialize by pointing to self
            nonlocal_root = [root]                  # make updateable non-locally
            PREV, NEXT, KEY, RESULT = 0, 1, 2, 3    # names for the link fields

            if maxsize == 0:

                def wrapper(*args, **kwds):
                    # no caching, just do a statistics update after a successful call
                    result = user_function(*args, **kwds)
                    stats[MISSES] += 1
                    return result

            elif maxsize is None:

                def wrapper(*args, **kwds):
                    # simple caching without ordering or size limit
                    key = make_key(args, kwds, typed)
                    result = cache_get(key, root)   # root used here as a unique not-found sentinel
                    if result is not root:
                        stats[HITS] += 1
                        return result
                    result = user_function(*args, **kwds)
                    cache[key] = result
                    stats[MISSES] += 1
                    return result

            else:

                def wrapper(*args, **kwds):
                    # size limited caching that tracks accesses by recency
                    key = make_key(args, kwds, typed) if kwds or typed else args
                    with lock:
                        link = cache_get(key)
                        if link is not None:
                            # record recent use of the key by moving it to the front of the list
                            root, = nonlocal_root
                            link_prev, link_next, key, result = link
                            link_prev[NEXT] = link_next
                            link_next[PREV] = link_prev
                            last = root[PREV]
                            last[NEXT] = root[PREV] = link
                            link[PREV] = last
                            link[NEXT] = root
                            stats[HITS] += 1
                            return result
                    result = user_function(*args, **kwds)
                    with lock:
                        root, = nonlocal_root
                        if key in cache:
                            # getting here means that this same key was added to the
                            # cache while the lock was released.  since the link
                            # update is already done, we need only return the
                            # computed result and update the count of misses.
                            pass
                        elif _len(cache) >= maxsize:
                            # use the old root to store the new key and result
                            oldroot = root
                            oldroot[KEY] = key
                            oldroot[RESULT] = result
                            # empty the oldest link and make it the new root
                            root = nonlocal_root[0] = oldroot[NEXT]
                            oldkey = root[KEY]
                            oldvalue = root[RESULT]
                            root[KEY] = root[RESULT] = None
                            # now update the cache dictionary for the new links
                            del cache[oldkey]
                            cache[key] = oldroot
                        else:
                            # put result in a new link at the front of the list
                            last = root[PREV]
                            link = [last, root, key, result]
                            last[NEXT] = root[PREV] = cache[key] = link
                        stats[MISSES] += 1
                    return result

            def cache_info():
                """Report cache statistics"""
                with lock:
                    return _CacheInfo(stats[HITS], stats[MISSES], maxsize, len(cache))

            def cache_clear():
                """Clear the cache and cache statistics"""
                with lock:
                    cache.clear()
                    root = nonlocal_root[0]
                    root[:] = [root, root, None, None]
                    stats[:] = [0, 0]

            wrapper.__wrapped__ = user_function
            wrapper.cache_info = cache_info
            wrapper.cache_clear = cache_clear
            return update_wrapper(wrapper, user_function)

        return decorating_function


# Markdown is optional
try:
    import markdown


    def apply_markdown(text):
        """
        Simple wrapper around :func:`markdown.markdown` to set the base level
        of '#' style headers to <h2>.
        """

        extensions = ['headerid(level=2)']
        safe_mode = False
        md = markdown.Markdown(extensions=extensions, safe_mode=safe_mode)
        return md.convert(text)
except ImportError:
    apply_markdown = None


# `separators` argument to `json.dumps()` differs between 2.x and 3.x
# See: http://bugs.python.org/issue22767
if six.PY3:
    SHORT_SEPARATORS = (',', ':')
    LONG_SEPARATORS = (', ', ': ')
    INDENT_SEPARATORS = (',', ': ')
else:
    SHORT_SEPARATORS = (b',', b':')
    LONG_SEPARATORS = (b', ', b': ')
    INDENT_SEPARATORS = (b',', b': ')

if django.VERSION >= (1, 8):
    from django.db.models import DurationField
    from django.utils.dateparse import parse_duration
    from django.utils.duration import duration_string
else:
    DurationField = duration_string = parse_duration = None


def set_rollback():
    if hasattr(transaction, 'set_rollback'):
        if connection.settings_dict.get('ATOMIC_REQUESTS', False):
            # If running in >=1.6 then mark a rollback as required,
            # and allow it to be handled by Django.
            if connection.in_atomic_block:
                transaction.set_rollback(True)
    elif transaction.is_managed():
        # Otherwise handle it explicitly if in managed mode.
        if transaction.is_dirty():
            transaction.rollback()
        transaction.leave_transaction_management()
    else:
        # transaction not managed
        pass
