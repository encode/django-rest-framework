"""
The `compat` module provides support for backwards compatibility with older
versions of django/python, and compatibility wrappers around optional packages.
"""

# flake8: noqa
from __future__ import unicode_literals
import django
import inspect
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.utils import six


# Handle django.utils.encoding rename in 1.5 onwards.
# smart_unicode -> smart_text
# force_unicode -> force_text
try:
    from django.utils.encoding import smart_text
except ImportError:
    from django.utils.encoding import smart_unicode as smart_text
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


# HttpResponseBase only exists from 1.5 onwards
try:
    from django.http.response import HttpResponseBase
except ImportError:
    from django.http import HttpResponse as HttpResponseBase


# django-filter is optional
try:
    import django_filters
except ImportError:
    django_filters = None


# Django-guardian is optional. Import only if guardian is in INSTALLED_APPS
# Fixes (#1712). We keep the try/except for the test suite.
guardian = None
if 'guardian' in settings.INSTALLED_APPS:
    try:
        import guardian
        import guardian.shortcuts  # Fixes #1624
    except ImportError:
        pass


# cStringIO only if it's available, otherwise StringIO
try:
    import cStringIO.StringIO as StringIO
except ImportError:
    StringIO = six.StringIO

BytesIO = six.BytesIO


# urlparse compat import (Required because it changed in python 3.x)
try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse

# UserDict moves in Python 3
try:
    from UserDict import UserDict
    from UserDict import DictMixin
except ImportError:
    from collections import UserDict
    from collections import MutableMapping as DictMixin

# Try to import PIL in either of the two ways it can end up installed.
try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except ImportError:
        Image = None


def get_model_name(model_cls):
    try:
        return model_cls._meta.model_name
    except AttributeError:
        # < 1.6 used module_name instead of model_name
        return model_cls._meta.module_name


def get_concrete_model(model_cls):
    try:
        return model_cls._meta.concrete_model
    except AttributeError:
        # 1.3 does not include concrete model
        return model_cls


# View._allowed_methods only present from 1.5 onwards
if django.VERSION >= (1, 5):
    from django.views.generic import View
else:
    from django.views.generic import View as DjangoView

    class View(DjangoView):
        def _allowed_methods(self):
            return [m.upper() for m in self.http_method_names if hasattr(self, m)]


# PATCH method is not implemented by Django
if 'patch' not in View.http_method_names:
    View.http_method_names = View.http_method_names + ['patch']


# RequestFactory only provides `generic` from 1.5 onwards
from django.test.client import RequestFactory as DjangoRequestFactory
from django.test.client import FakePayload
try:
    # In 1.5 the test client uses force_bytes
    from django.utils.encoding import force_bytes as force_bytes_or_smart_bytes
except ImportError:
    # In 1.4 the test client just uses smart_str
    from django.utils.encoding import smart_str as force_bytes_or_smart_bytes

class RequestFactory(DjangoRequestFactory):
    def generic(self, method, path,
            data='', content_type='application/octet-stream', **extra):
        parsed = urlparse.urlparse(path)
        data = force_bytes_or_smart_bytes(data, settings.DEFAULT_CHARSET)
        r = {
            'PATH_INFO':      self._get_path(parsed),
            'QUERY_STRING':   force_text(parsed[4]),
            'REQUEST_METHOD': str(method),
        }
        if data:
            r.update({
                'CONTENT_LENGTH': len(data),
                'CONTENT_TYPE':   str(content_type),
                'wsgi.input':     FakePayload(data),
            })
        elif django.VERSION <= (1, 4):
            # For 1.3 we need an empty WSGI payload
            r.update({
                'wsgi.input': FakePayload('')
            })
        r.update(extra)
        return self.request(**r)


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


# Yaml is optional
try:
    import yaml
except ImportError:
    yaml = None


# XML is optional
try:
    import defusedxml.ElementTree as etree
except ImportError:
    etree = None


# OAuth2 is optional
try:
    # Note: The `oauth2` package actually provides oauth1.0a support.  Urg.
    import oauth2 as oauth
except ImportError:
    oauth = None


# OAuthProvider is optional
try:
    import oauth_provider
    from oauth_provider.store import store as oauth_provider_store

    # check_nonce's calling signature in django-oauth-plus changes sometime
    # between versions 2.0 and 2.2.1
    def check_nonce(request, oauth_request, oauth_nonce, oauth_timestamp):
        check_nonce_args = inspect.getargspec(oauth_provider_store.check_nonce).args
        if 'timestamp' in check_nonce_args:
            return oauth_provider_store.check_nonce(
                request, oauth_request, oauth_nonce, oauth_timestamp
            )
        return oauth_provider_store.check_nonce(
            request, oauth_request, oauth_nonce
        )

except (ImportError, ImproperlyConfigured):
    oauth_provider = None
    oauth_provider_store = None
    check_nonce = None


# OAuth 2 support is optional
try:
    import provider as oauth2_provider
    from provider import scope as oauth2_provider_scope
    from provider import constants as oauth2_constants
    if oauth2_provider.__version__ in ('0.2.3', '0.2.4'):
        # 0.2.3 and 0.2.4 are supported version that do not support
        # timezone aware datetimes
        import datetime
        provider_now = datetime.datetime.now
    else:
        # Any other supported version does use timezone aware datetimes
        from django.utils.timezone import now as provider_now
except ImportError:
    oauth2_provider = None
    oauth2_provider_scope = None
    oauth2_constants = None
    provider_now = None


# Handle lazy strings across Py2/Py3
from django.utils.functional import Promise

if six.PY3:
    def is_non_str_iterable(obj):
        if (isinstance(obj, str) or
            (isinstance(obj, Promise) and obj._delegate_text)):
            return False
        return hasattr(obj, '__iter__')
else:
    def is_non_str_iterable(obj):
        return hasattr(obj, '__iter__')


try:
    from django.utils.encoding import python_2_unicode_compatible
except ImportError:
    def python_2_unicode_compatible(klass):
        """
        A decorator that defines __unicode__ and __str__ methods under Python 2.
        Under Python 3 it does nothing.

        To support Python 2 and 3 with a single code base, define a __str__ method
        returning text and apply this decorator to the class.
        """
        if '__str__' not in klass.__dict__:
            raise ValueError("@python_2_unicode_compatible cannot be applied "
                             "to %s because it doesn't define __str__()." %
                             klass.__name__)
        klass.__unicode__ = klass.__str__
        klass.__str__ = lambda self: self.__unicode__().encode('utf-8')
        return klass

"""
SortedDict deprecated since django 1.8. There is collections.OrderedDict
which available since python 2.7 and python 3.1. There are no need of other
checks because of django 1.7+ requires python 2.7+
"""
try:
    from collections import OrderedDict as SortedDict
except ImportError:
    from django.utils.datastructures import SortedDict

"""
GenericForeignKey moves from generic to fields in django 1.9 and in 1.8 shows
deprecation warnings
"""
if django.VERSION >= (1, 8):
    from django.contrib.contenttypes.fields import GenericForeignKey
else:
    from django.contrib.contenttypes.generic import GenericForeignKey

"""
django.utils.importlib is deprecated since django 1.8
"""
try:
    import importlib
except ImportError:
    from django.utils import importlib
