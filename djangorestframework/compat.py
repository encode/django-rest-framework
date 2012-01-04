"""
The :mod:`compat` module provides support for backwards compatibility with older versions of django/python.
"""
import django

# cStringIO only if it's available, otherwise StringIO
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO


# parse_qs from 'urlparse' module unless python 2.5, in which case from 'cgi'
try:
    # python >= 2.6
    from urlparse import parse_qs
except ImportError:
    # python < 2.6
    from cgi import parse_qs


# django.test.client.RequestFactory (Required for Django < 1.3)
try:
    from django.test.client import RequestFactory
except ImportError:
    from django.test import Client
    from django.core.handlers.wsgi import WSGIRequest

    # From: http://djangosnippets.org/snippets/963/
    # Lovely stuff
    class RequestFactory(Client):
        """
        Class that lets you create mock :obj:`Request` objects for use in testing.

        Usage::

            rf = RequestFactory()
            get_request = rf.get('/hello/')
            post_request = rf.post('/submit/', {'foo': 'bar'})

        This class re-uses the :class:`django.test.client.Client` interface. Of which
        you can find the docs here__.

        __ http://www.djangoproject.com/documentation/testing/#the-test-client

        Once you have a `request` object you can pass it to any :func:`view` function,
        just as if that :func:`view` had been hooked up using a URLconf.
        """
        def request(self, **request):
            """
            Similar to parent class, but returns the :obj:`request` object as soon as it
            has created it.
            """
            environ = {
                'HTTP_COOKIE': self.cookies,
                'PATH_INFO': '/',
                'QUERY_STRING': '',
                'REQUEST_METHOD': 'GET',
                'SCRIPT_NAME': '',
                'SERVER_NAME': 'testserver',
                'SERVER_PORT': 80,
                'SERVER_PROTOCOL': 'HTTP/1.1',
            }
            environ.update(self.defaults)
            environ.update(request)
            return WSGIRequest(environ)

# django.views.generic.View (Django >= 1.3)
try:
    from django.views.generic import View
    if not hasattr(View, 'head'):
        # First implementation of Django class-based views did not include head method
        # in base View class - https://code.djangoproject.com/ticket/15668
        class ViewPlusHead(View):
            def head(self, request, *args, **kwargs):
                return self.get(request, *args, **kwargs)
        View = ViewPlusHead

except ImportError:
    from django import http
    from django.utils.functional import update_wrapper
    # from django.utils.log import getLogger
    # from django.utils.decorators import classonlymethod

    # logger = getLogger('django.request') - We'll just drop support for logger if running Django <= 1.2
    # Might be nice to fix this up sometime to allow djangorestframework.compat.View to match 1.3's View more closely

    class View(object):
        """
        Intentionally simple parent class for all views. Only implements
        dispatch-by-method and simple sanity checking.
        """

        http_method_names = ['get', 'post', 'put', 'delete', 'head', 'options', 'trace']

        def __init__(self, **kwargs):
            """
            Constructor. Called in the URLconf; can contain helpful extra
            keyword arguments, and other things.
            """
            # Go through keyword arguments, and either save their values to our
            # instance, or raise an error.
            for key, value in kwargs.iteritems():
                setattr(self, key, value)

        # @classonlymethod - We'll just us classmethod instead if running Django <= 1.2
        @classmethod
        def as_view(cls, **initkwargs):
            """
            Main entry point for a request-response process.
            """
            # sanitize keyword arguments
            for key in initkwargs:
                if key in cls.http_method_names:
                    raise TypeError(u"You tried to pass in the %s method name as a "
                                    u"keyword argument to %s(). Don't do that."
                                    % (key, cls.__name__))
                if not hasattr(cls, key):
                    raise TypeError(u"%s() received an invalid keyword %r" % (
                        cls.__name__, key))

            def view(request, *args, **kwargs):
                self = cls(**initkwargs)
                return self.dispatch(request, *args, **kwargs)

            # take name and docstring from class
            update_wrapper(view, cls, updated=())

            # and possible attributes set by decorators
            # like csrf_exempt from dispatch
            update_wrapper(view, cls.dispatch, assigned=())
            return view

        def dispatch(self, request, *args, **kwargs):
            # Try to dispatch to the right method; if a method doesn't exist,
            # defer to the error handler. Also defer to the error handler if the
            # request method isn't on the approved list.
            if request.method.lower() in self.http_method_names:
                handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
            else:
                handler = self.http_method_not_allowed
            self.request = request
            self.args = args
            self.kwargs = kwargs
            return handler(request, *args, **kwargs)

        def http_method_not_allowed(self, request, *args, **kwargs):
            allowed_methods = [m for m in self.http_method_names if hasattr(self, m)]
            #logger.warning('Method Not Allowed (%s): %s' % (request.method, request.path),
            #    extra={
            #        'status_code': 405,
            #        'request': self.request
            #    }
            #)
            return http.HttpResponseNotAllowed(allowed_methods)

        def head(self, request, *args, **kwargs):
            return self.get(request, *args, **kwargs)

# PUT, DELETE do not require CSRF until 1.4.  They should.  Make it better.
if django.VERSION >= (1, 4):
    from django.middleware.csrf import CsrfViewMiddleware
else:
    import hashlib
    import re
    import random
    import logging
    import urlparse

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
    _MAX_CSRF_KEY = 18446744073709551616L     # 2 << 63

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


# Markdown is optional
try:
    import markdown

    class CustomSetextHeaderProcessor(markdown.blockprocessors.BlockProcessor):
        """
        Class for markdown < 2.1

        Override `markdown`'s :class:`SetextHeaderProcessor`, so that ==== headers are <h2> and ---- heade

        We use <h1> for the resource name.
        """
        import re
        # Detect Setext-style header. Must be first 2 lines of block.
        RE = re.compile(r'^.*?\n[=-]{3,}', re.MULTILINE)

        def test(self, parent, block):
            return bool(self.RE.match(block))

        def run(self, parent, blocks):
            lines = blocks.pop(0).split('\n')
            # Determine level. ``=`` is 1 and ``-`` is 2.
            if lines[1].startswith('='):
                level = 2
            else:
                level = 3
            h = markdown.etree.SubElement(parent, 'h%d' % level)
            h.text = lines[0].strip()
            if len(lines) > 2:
                # Block contains additional lines. Add to  master blocks for later.
                blocks.insert(0, '\n'.join(lines[2:]))

    def apply_markdown(text):
        """
        Simple wrapper around :func:`markdown.markdown` to set the base level
        of '#' style headers to <h2>.
        """

        extensions = ['headerid(level=2)']
        safe_mode = False,

        if markdown.version_info < (2, 1):
            output_format = markdown.DEFAULT_OUTPUT_FORMAT

            md = markdown.Markdown(extensions=markdown.load_extensions(extensions),
                               safe_mode=safe_mode,
                               output_format=output_format)
            md.parser.blockprocessors['setextheader'] = CustomSetextHeaderProcessor(md.parser)
        else:
            md = markdown.Markdown(extensions=extensions, safe_mode=safe_mode)
        return md.convert(text)

except ImportError:
    apply_markdown = None

# Yaml is optional
try:
    import yaml
except ImportError:
    yaml = None

import unittest
try:
    import unittest.skip
except ImportError: # python < 2.7
    from unittest import TestCase
    import functools 

    def skip(reason):
        # Pasted from py27/lib/unittest/case.py
        """
        Unconditionally skip a test.
        """
        def decorator(test_item):
            if not (isinstance(test_item, type) and issubclass(test_item, TestCase)):
                @functools.wraps(test_item)
                def skip_wrapper(*args, **kwargs):
                   pass 
                test_item = skip_wrapper

            test_item.__unittest_skip__ = True
            test_item.__unittest_skip_why__ = reason
            return test_item
        return decorator
     
    unittest.skip = skip
