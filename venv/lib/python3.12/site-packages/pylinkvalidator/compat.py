# -*- coding: utf-8 -*-
# flake8: noqa
"""
Contains the compatibility layer for python 2 & 3
"""
from __future__ import unicode_literals, absolute_import

import sys

if sys.version_info[0] < 3:
    range = xrange
    import urlparse
    from urllib import quote
    import SimpleHTTPServer
    import SocketServer
    from urllib2 import HTTPError
    import Queue
    unicode = unicode

    def get_content_type(m):
        return m.gettype()

    def get_charset(m):
        return m.getparam("charset")

    def get_safe_str(s):
        return s.encode("utf-8")

    from StringIO import StringIO
else:
    range = range
    import urllib.parse as urlparse
    from urllib.parse import quote
    import http.server as SimpleHTTPServer
    import socketserver as SocketServer
    from urllib.error import HTTPError
    import queue as Queue
    unicode = str

    def get_content_type(m):
        return m.get_content_type()

    def get_charset(m):
        return m.get_content_charset()

    def get_safe_str(s):
        return s
    from io import StringIO

try:
    from logging import NullHandler
except ImportError:
    from logging import Handler

    class NullHandler(Handler):
        def emit(self, record):
            pass

        def handle(self, record):
            pass

        def createLock(self):
            return None


def get_url_open():
    # Not automatically imported to allow monkey patching.
    if sys.version_info[0] < 3:
        from urllib2 import urlopen
    else:
        from urllib.request import urlopen
    return urlopen


def get_url_request():
    if sys.version_info[0] < 3:
        from urllib2 import Request
    else:
        from urllib.request import Request
    return Request
