"""
The `compat` module provides support for backwards compatibility with older
versions of django/python, and compatibility wrappers around optional packages.
"""
# flake8: noqa
from __future__ import unicode_literals

import django

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


# django-filter is optional
try:
    import django_filters
except ImportError:
    django_filters = None


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
    from django.conf import settings
    if hasattr(settings, 'AUTH_USER_MODEL'):
        User = settings.AUTH_USER_MODEL
    else:
        from django.contrib.auth.models import User
else:
    try:
        from django.contrib.auth.models import User
    except ImportError:
        raise ImportError("User model is not to be found.")


# First implementation of Django class-based views did not include head method
# in base View class - https://code.djangoproject.com/ticket/15668
if django.VERSION >= (1, 4):
    from django.views.generic import View
else:
    from django.views.generic import View as _View
    from django.utils.decorators import classonlymethod
    from django.utils.functional import update_wrapper

    class View(_View):
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

# Taken from @markotibold's attempt at supporting PATCH.
# https://github.com/markotibold/django-rest-framework/tree/patch
http_method_names = set(View.http_method_names)
http_method_names.add('patch')
View.http_method_names = list(http_method_names)  # PATCH method is not implemented by Django

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
