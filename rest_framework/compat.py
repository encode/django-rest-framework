"""
The `compat` module provides support for backwards compatibility with older
versions of django/python, and compatibility wrappers around optional packages.
"""

# flake8: noqa
from __future__ import unicode_literals

import django
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

# Try to import six from Django, fallback to included `six`.
try:
    from django.utils import six
except ImportError:
    from rest_framework import six

# location of patterns, url, include changes in 1.4 onwards
try:
    from django.conf.urls import patterns, url, include
except ImportError:
    from django.conf.urls.defaults import patterns, url, include

# Handle django.utils.encoding rename:
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

# guardian is optional
try:
    import guardian
except ImportError:
    guardian = None


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


# Try to import PIL in either of the two ways it can end up installed.
try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except ImportError:
        Image = None


def get_concrete_model(model_cls):
    try:
        return model_cls._meta.concrete_model
    except AttributeError:
        # 1.3 does not include concrete model
        return model_cls


# Django 1.5 add support for custom auth user model
if django.VERSION >= (1, 5):
    AUTH_USER_MODEL = settings.AUTH_USER_MODEL
else:
    AUTH_USER_MODEL = 'auth.User'


if django.VERSION >= (1, 5):
    from django.views.generic import View
else:
    from django.views.generic import View as _View
    from django.utils.decorators import classonlymethod
    from django.utils.functional import update_wrapper

    class View(_View):
        # 1.3 does not include head method in base View class
        # See: https://code.djangoproject.com/ticket/15668
        @classonlymethod
        def as_view(cls, **initkwargs):
            """
            Main entry point for a request-response process.
            """
            # sanitize keyword arguments
            for key in initkwargs:
                if key in cls.http_method_names:
                    raise TypeError("You tried to pass in the %s method name as a "
                                    "keyword argument to %s(). Don't do that."
                                    % (key, cls.__name__))
                if not hasattr(cls, key):
                    raise TypeError("%s() received an invalid keyword %r" % (
                        cls.__name__, key))

            def view(request, *args, **kwargs):
                self = cls(**initkwargs)
                if hasattr(self, 'get') and not hasattr(self, 'head'):
                    self.head = self.get
                return self.dispatch(request, *args, **kwargs)

            # take name and docstring from class
            update_wrapper(view, cls, updated=())

            # and possible attributes set by decorators
            # like csrf_exempt from dispatch
            update_wrapper(view, cls.dispatch, assigned=())
            return view

        # _allowed_methods only present from 1.5 onwards
        def _allowed_methods(self):
            return [m.upper() for m in self.http_method_names if hasattr(self, m)]


# PATCH method is not implemented by Django
if 'patch' not in View.http_method_names:
    View.http_method_names = View.http_method_names + ['patch']


# PUT, DELETE do not require CSRF until 1.4.  They should.  Make it better.
if django.VERSION >= (1, 4):
    from django.middleware.csrf import CsrfViewMiddleware
else:
    import hashlib
    import re
    import random
    import logging

    from django.conf import settings
    from django.core.urlresolvers import get_callable

    try:
        from logging import NullHandler
    except ImportError:
        class NullHandler(logging.Handler):
            def emit(self, record):
                pass

    logger = logging.getLogger('django.request')

    if not logger.handlers:
        logger.addHandler(NullHandler())

    def same_origin(url1, url2):
        """
        Checks if two URLs are 'same-origin'
        """
        p1, p2 = urlparse.urlparse(url1), urlparse.urlparse(url2)
        return p1[0:2] == p2[0:2]

    def constant_time_compare(val1, val2):
        """
        Returns True if the two strings are equal, False otherwise.

        The time taken is independent of the number of characters that match.
        """
        if len(val1) != len(val2):
            return False
        result = 0
        for x, y in zip(val1, val2):
            result |= ord(x) ^ ord(y)
        return result == 0

    # Use the system (hardware-based) random number generator if it exists.
    if hasattr(random, 'SystemRandom'):
        randrange = random.SystemRandom().randrange
    else:
        randrange = random.randrange

    _MAX_CSRF_KEY = 18446744073709551616      # 2 << 63

    REASON_NO_REFERER = "Referer checking failed - no Referer."
    REASON_BAD_REFERER = "Referer checking failed - %s does not match %s."
    REASON_NO_CSRF_COOKIE = "CSRF cookie not set."
    REASON_BAD_TOKEN = "CSRF token missing or incorrect."

    def _get_failure_view():
        """
        Returns the view to be used for CSRF rejections
        """
        return get_callable(settings.CSRF_FAILURE_VIEW)

    def _get_new_csrf_key():
        return hashlib.md5("%s%s" % (randrange(0, _MAX_CSRF_KEY), settings.SECRET_KEY)).hexdigest()

    def get_token(request):
        """
        Returns the the CSRF token required for a POST form. The token is an
        alphanumeric value.

        A side effect of calling this function is to make the the csrf_protect
        decorator and the CsrfViewMiddleware add a CSRF cookie and a 'Vary: Cookie'
        header to the outgoing response.  For this reason, you may need to use this
        function lazily, as is done by the csrf context processor.
        """
        request.META["CSRF_COOKIE_USED"] = True
        return request.META.get("CSRF_COOKIE", None)

    def _sanitize_token(token):
        # Allow only alphanum, and ensure we return a 'str' for the sake of the post
        # processing middleware.
        token = re.sub('[^a-zA-Z0-9]', '', str(token.decode('ascii', 'ignore')))
        if token == "":
            # In case the cookie has been truncated to nothing at some point.
            return _get_new_csrf_key()
        else:
            return token

    class CsrfViewMiddleware(object):
        """
        Middleware that requires a present and correct csrfmiddlewaretoken
        for POST requests that have a CSRF cookie, and sets an outgoing
        CSRF cookie.

        This middleware should be used in conjunction with the csrf_token template
        tag.
        """
        # The _accept and _reject methods currently only exist for the sake of the
        # requires_csrf_token decorator.
        def _accept(self, request):
            # Avoid checking the request twice by adding a custom attribute to
            # request.  This will be relevant when both decorator and middleware
            # are used.
            request.csrf_processing_done = True
            return None

        def _reject(self, request, reason):
            return _get_failure_view()(request, reason=reason)

        def process_view(self, request, callback, callback_args, callback_kwargs):

            if getattr(request, 'csrf_processing_done', False):
                return None

            try:
                csrf_token = _sanitize_token(request.COOKIES[settings.CSRF_COOKIE_NAME])
                # Use same token next time
                request.META['CSRF_COOKIE'] = csrf_token
            except KeyError:
                csrf_token = None
                # Generate token and store it in the request, so it's available to the view.
                request.META["CSRF_COOKIE"] = _get_new_csrf_key()

            # Wait until request.META["CSRF_COOKIE"] has been manipulated before
            # bailing out, so that get_token still works
            if getattr(callback, 'csrf_exempt', False):
                return None

            # Assume that anything not defined as 'safe' by RC2616 needs protection.
            if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
                if getattr(request, '_dont_enforce_csrf_checks', False):
                    # Mechanism to turn off CSRF checks for test suite.  It comes after
                    # the creation of CSRF cookies, so that everything else continues to
                    # work exactly the same (e.g. cookies are sent etc), but before the
                    # any branches that call reject()
                    return self._accept(request)

                if request.is_secure():
                    # Suppose user visits http://example.com/
                    # An active network attacker,(man-in-the-middle, MITM) sends a
                    # POST form which targets https://example.com/detonate-bomb/ and
                    # submits it via javascript.
                    #
                    # The attacker will need to provide a CSRF cookie and token, but
                    # that is no problem for a MITM and the session independent
                    # nonce we are using. So the MITM can circumvent the CSRF
                    # protection. This is true for any HTTP connection, but anyone
                    # using HTTPS expects better!  For this reason, for
                    # https://example.com/ we need additional protection that treats
                    # http://example.com/ as completely untrusted.  Under HTTPS,
                    # Barth et al. found that the Referer header is missing for
                    # same-domain requests in only about 0.2% of cases or less, so
                    # we can use strict Referer checking.
                    referer = request.META.get('HTTP_REFERER')
                    if referer is None:
                        logger.warning('Forbidden (%s): %s' % (REASON_NO_REFERER, request.path),
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, REASON_NO_REFERER)

                    # Note that request.get_host() includes the port
                    good_referer = 'https://%s/' % request.get_host()
                    if not same_origin(referer, good_referer):
                        reason = REASON_BAD_REFERER % (referer, good_referer)
                        logger.warning('Forbidden (%s): %s' % (reason, request.path),
                            extra={
                                'status_code': 403,
                                'request': request,
                            }
                        )
                        return self._reject(request, reason)

                if csrf_token is None:
                    # No CSRF cookie. For POST requests, we insist on a CSRF cookie,
                    # and in this way we can avoid all CSRF attacks, including login
                    # CSRF.
                    logger.warning('Forbidden (%s): %s' % (REASON_NO_CSRF_COOKIE, request.path),
                        extra={
                            'status_code': 403,
                            'request': request,
                        }
                    )
                    return self._reject(request, REASON_NO_CSRF_COOKIE)

                # check non-cookie token for match
                request_csrf_token = ""
                if request.method == "POST":
                    request_csrf_token = request.POST.get('csrfmiddlewaretoken', '')

                if request_csrf_token == "":
                    # Fall back to X-CSRFToken, to make things easier for AJAX,
                    # and possible for PUT/DELETE
                    request_csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')

                if not constant_time_compare(request_csrf_token, csrf_token):
                    logger.warning('Forbidden (%s): %s' % (REASON_BAD_TOKEN, request.path),
                        extra={
                            'status_code': 403,
                            'request': request,
                        }
                    )
                    return self._reject(request, REASON_BAD_TOKEN)

            return self._accept(request)

# timezone support is new in Django 1.4
try:
    from django.utils import timezone
except ImportError:
    timezone = None

# dateparse is ALSO new in Django 1.4
try:
    from django.utils.dateparse import parse_date, parse_datetime, parse_time
except ImportError:
    import datetime
    import re

    date_re = re.compile(
        r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})$'
    )

    datetime_re = re.compile(
        r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})'
        r'[T ](?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
        r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
        r'(?P<tzinfo>Z|[+-]\d{1,2}:\d{1,2})?$'
    )

    time_re = re.compile(
        r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2})'
        r'(?::(?P<second>\d{1,2})(?:\.(?P<microsecond>\d{1,6})\d{0,6})?)?'
    )

    def parse_date(value):
        match = date_re.match(value)
        if match:
            kw = dict((k, int(v)) for k, v in match.groupdict().iteritems())
            return datetime.date(**kw)

    def parse_time(value):
        match = time_re.match(value)
        if match:
            kw = match.groupdict()
            if kw['microsecond']:
                kw['microsecond'] = kw['microsecond'].ljust(6, '0')
            kw = dict((k, int(v)) for k, v in kw.iteritems() if v is not None)
            return datetime.time(**kw)

    def parse_datetime(value):
        """Parse datetime, but w/o the timezone awareness in 1.4"""
        match = datetime_re.match(value)
        if match:
            kw = match.groupdict()
            if kw['microsecond']:
                kw['microsecond'] = kw['microsecond'].ljust(6, '0')
            kw = dict((k, int(v)) for k, v in kw.iteritems() if v is not None)
            return datetime.datetime(**kw)


# smart_urlquote is new on Django 1.4
try:
    from django.utils.html import smart_urlquote
except ImportError:
    import re
    from django.utils.encoding import smart_str
    try:
        from urllib.parse import quote, urlsplit, urlunsplit
    except ImportError:     # Python 2
        from urllib import quote
        from urlparse import urlsplit, urlunsplit

    unquoted_percents_re = re.compile(r'%(?![0-9A-Fa-f]{2})')

    def smart_urlquote(url):
        "Quotes a URL if it isn't already quoted."
        # Handle IDN before quoting.
        scheme, netloc, path, query, fragment = urlsplit(url)
        try:
            netloc = netloc.encode('idna').decode('ascii')  # IDN -> ACE
        except UnicodeError:  # invalid domain part
            pass
        else:
            url = urlunsplit((scheme, netloc, path, query, fragment))

        # An URL is considered unquoted if it contains no % characters or
        # contains a % not followed by two hexadecimal digits. See #9655.
        if '%' not in url or unquoted_percents_re.search(url):
            # See http://bugs.python.org/issue2637
            url = quote(smart_str(url), safe=b'!*\'();:@&=+$,/?#[]~')

        return force_text(url)


# RequestFactory only provide `generic` from 1.5 onwards

from django.test.client import RequestFactory as DjangoRequestFactory
from django.test.client import FakePayload
try:
    # In 1.5 the test client uses force_bytes
    from django.utils.encoding import force_bytes_or_smart_bytes
except ImportError:
    # In 1.3 and 1.4 the test client just uses smart_str
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

# OAuth is optional
try:
    # Note: The `oauth2` package actually provides oauth1.0a support.  Urg.
    import oauth2 as oauth
except ImportError:
    oauth = None

# OAuth is optional
try:
    import oauth_provider
    from oauth_provider.store import store as oauth_provider_store
except (ImportError, ImproperlyConfigured):
    oauth_provider = None
    oauth_provider_store = None

# OAuth 2 support is optional
try:
    import provider.oauth2 as oauth2_provider
    from provider.oauth2 import models as oauth2_provider_models
    from provider.oauth2 import forms as oauth2_provider_forms
    from provider import scope as oauth2_provider_scope
    from provider import constants as oauth2_constants
    from provider import __version__ as provider_version
    if provider_version in ('0.2.3', '0.2.4'):
        # 0.2.3 and 0.2.4 are supported version that do not support
        # timezone aware datetimes
        import datetime
        provider_now = datetime.datetime.now
    else:
        # Any other supported version does use timezone aware datetimes
        from django.utils.timezone import now as provider_now
except ImportError:
    oauth2_provider = None
    oauth2_provider_models = None
    oauth2_provider_forms = None
    oauth2_provider_scope = None
    oauth2_constants = None
    provider_now = None

# Handle lazy strings
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
