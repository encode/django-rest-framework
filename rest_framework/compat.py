"""
The `compat` module provides support for backwards compatibility with older
versions of django/python, and compatibility wrappers around optional packages.
"""

# flake8: noqa
from __future__ import unicode_literals

import inspect

from django.core.exceptions import ImproperlyConfigured
from django.utils.encoding import force_text
from django.utils.six.moves.urllib.parse import urlparse as _urlparse
from django.conf import settings
from django.utils import six
import django


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


def total_seconds(timedelta):
    # TimeDelta.total_seconds() is only available in Python 2.7
    if hasattr(timedelta, 'total_seconds'):
        return timedelta.total_seconds()
    else:
        return (timedelta.days * 86400.0) + float(timedelta.seconds) + (timedelta.microseconds / 1000000.0)


# OrderedDict only available in Python 2.7.
# This will always be the case in Django 1.7 and above, as these versions
# no longer support Python 2.6.
# For Django <= 1.6 and Python 2.6 fall back to SortedDict.
try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict


# HttpResponseBase only exists from 1.5 onwards
try:
    from django.http.response import HttpResponseBase
except ImportError:
    from django.http import HttpResponse as HttpResponseBase


# contrib.postgres only supported from 1.8 onwards.
try:
    from django.contrib.postgres import fields as postgres_fields
except ImportError:
    postgres_fields = None


# request only provides `resolver_match` from 1.5 onwards.
def get_resolver_match(request):
    try:
        return request.resolver_match
    except AttributeError:
        # Django < 1.5
        from django.core.urlresolvers import resolve
        return resolve(request.path_info)


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


# View._allowed_methods only present from 1.5 onwards
if django.VERSION >= (1, 5):
    from django.views.generic import View
else:
    from django.views.generic import View as DjangoView

    class View(DjangoView):
        def _allowed_methods(self):
            return [m.upper() for m in self.http_method_names if hasattr(self, m)]


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
        parsed = _urlparse(path)
        data = force_bytes_or_smart_bytes(data, settings.DEFAULT_CHARSET)
        r = {
            'PATH_INFO': self._get_path(parsed),
            'QUERY_STRING': force_text(parsed[4]),
            'REQUEST_METHOD': six.text_type(method),
        }
        if data:
            r.update({
                'CONTENT_LENGTH': len(data),
                'CONTENT_TYPE': six.text_type(content_type),
                'wsgi.input': FakePayload(data),
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

# `separators` argument to `json.dumps()` differs between 2.x and 3.x
# See: http://bugs.python.org/issue22767
if six.PY3:
    SHORT_SEPARATORS = (',', ':')
    LONG_SEPARATORS = (', ', ': ')
else:
    SHORT_SEPARATORS = (b',', b':')
    LONG_SEPARATORS = (b', ', b': ')
