# coding: utf-8

import base64


__all__ = [
    'urlparse', 'string_types',
    'COMPACT_SEPARATORS', 'VERBOSE_SEPARATORS'
]


try:
    # Python 2
    import urlparse
    import cookielib as cookiejar

    string_types = (basestring,)
    text_type = unicode
    COMPACT_SEPARATORS = (b',', b':')
    VERBOSE_SEPARATORS = (b',', b': ')

    def b64encode(input_string):
        # Provide a consistently-as-unicode interface across 2.x and 3.x
        return base64.b64encode(input_string)

except ImportError:
    # Python 3
    import urllib.parse as urlparse
    from io import IOBase
    from http import cookiejar

    string_types = (str,)
    text_type = str
    COMPACT_SEPARATORS = (',', ':')
    VERBOSE_SEPARATORS = (',', ': ')

    def b64encode(input_string):
        # Provide a consistently-as-unicode interface across 2.x and 3.x
        return base64.b64encode(input_string.encode('ascii')).decode('ascii')


def force_bytes(string):
    if isinstance(string, string_types):
        return string.encode('utf-8')
    return string


def force_text(string):
    if not isinstance(string, string_types):
        return string.decode('utf-8')
    return string


try:
    import click
    console_style = click.style
except ImportError:
    def console_style(text, **kwargs):
        return text


try:
    from tempfile import _TemporaryFileWrapper
except ImportError:
    _TemporaryFileWrapper = None
