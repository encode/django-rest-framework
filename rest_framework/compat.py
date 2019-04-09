"""
The `compat` module provides support for backwards compatibility with older
versions of Django/Python, and compatibility wrappers around optional packages.
"""

from __future__ import unicode_literals

import sys

from django.conf import settings
from django.core import validators
from django.utils import six
from django.views.generic import View

try:
    # Python 3
    from collections.abc import Mapping, MutableMapping   # noqa
except ImportError:
    # Python 2.7
    from collections import Mapping, MutableMapping   # noqa

try:
    from django.urls import (  # noqa
        URLPattern,
        URLResolver,
    )
except ImportError:
    # Will be removed in Django 2.0
    from django.urls import (  # noqa
        RegexURLPattern as URLPattern,
        RegexURLResolver as URLResolver,
    )

try:
    from django.core.validators import ProhibitNullCharactersValidator  # noqa
except ImportError:
    ProhibitNullCharactersValidator = None

try:
    from unittest import mock
except ImportError:
    mock = None


def get_original_route(urlpattern):
    """
    Get the original route/regex that was typed in by the user into the path(), re_path() or url() directive. This
    is in contrast with get_regex_pattern below, which for RoutePattern returns the raw regex generated from the path().
    """
    if hasattr(urlpattern, 'pattern'):
        # Django 2.0
        return str(urlpattern.pattern)
    else:
        # Django < 2.0
        return urlpattern.regex.pattern


def get_regex_pattern(urlpattern):
    """
    Get the raw regex out of the urlpattern's RegexPattern or RoutePattern. This is always a regular expression,
    unlike get_original_route above.
    """
    if hasattr(urlpattern, 'pattern'):
        # Django 2.0
        return urlpattern.pattern.regex.pattern
    else:
        # Django < 2.0
        return urlpattern.regex.pattern


def is_route_pattern(urlpattern):
    if hasattr(urlpattern, 'pattern'):
        # Django 2.0
        from django.urls.resolvers import RoutePattern
        return isinstance(urlpattern.pattern, RoutePattern)
    else:
        # Django < 2.0
        return False


def make_url_resolver(regex, urlpatterns):
    try:
        # Django 2.0
        from django.urls.resolvers import RegexPattern
        return URLResolver(RegexPattern(regex), urlpatterns)

    except ImportError:
        # Django < 2.0
        return URLResolver(regex, urlpatterns)


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
    if isinstance(value, bytes):
        return value.decode('iso-8859-1')
    return value


def distinct(queryset, base):
    if settings.DATABASES[queryset.db]["ENGINE"] == "django.db.backends.oracle":
        # distinct analogue for Oracle users
        return base.filter(pk__in=set(queryset.values_list('pk', flat=True)))
    return queryset.distinct()


# django.contrib.postgres requires psycopg2
try:
    from django.contrib.postgres import fields as postgres_fields
except ImportError:
    postgres_fields = None


# coreapi is optional (Note that uritemplate is a dependency of coreapi)
try:
    import coreapi
    import uritemplate
except ImportError:
    coreapi = None
    uritemplate = None


# coreschema is optional
try:
    import coreschema
except ImportError:
    coreschema = None


# pyyaml is optional
try:
    import yaml
except ImportError:
    yaml = None


# django-crispy-forms is optional
try:
    import crispy_forms
except ImportError:
    crispy_forms = None


# requests is optional
try:
    import requests
except ImportError:
    requests = None


def is_guardian_installed():
    """
    django-guardian is optional and only imported if in INSTALLED_APPS.
    """
    if six.PY2:
        # Guardian 1.5.0, for Django 2.2 is NOT compatible with Python 2.7.
        # Remove when dropping PY2.
        return False
    return 'guardian' in settings.INSTALLED_APPS


# PATCH method is not implemented by Django
if 'patch' not in View.http_method_names:
    View.http_method_names = View.http_method_names + ['patch']


# Markdown is optional
try:
    import markdown

    if markdown.version <= '2.2':
        HEADERID_EXT_PATH = 'headerid'
        LEVEL_PARAM = 'level'
    elif markdown.version < '2.6':
        HEADERID_EXT_PATH = 'markdown.extensions.headerid'
        LEVEL_PARAM = 'level'
    else:
        HEADERID_EXT_PATH = 'markdown.extensions.toc'
        LEVEL_PARAM = 'baselevel'

    def apply_markdown(text):
        """
        Simple wrapper around :func:`markdown.markdown` to set the base level
        of '#' style headers to <h2>.
        """
        extensions = [HEADERID_EXT_PATH]
        extension_configs = {
            HEADERID_EXT_PATH: {
                LEVEL_PARAM: '2'
            }
        }
        md = markdown.Markdown(
            extensions=extensions, extension_configs=extension_configs
        )
        md_filter_add_syntax_highlight(md)
        return md.convert(text)
except ImportError:
    apply_markdown = None
    markdown = None


try:
    import pygments
    from pygments.lexers import get_lexer_by_name, TextLexer
    from pygments.formatters import HtmlFormatter

    def pygments_highlight(text, lang, style):
        lexer = get_lexer_by_name(lang, stripall=False)
        formatter = HtmlFormatter(nowrap=True, style=style)
        return pygments.highlight(text, lexer, formatter)

    def pygments_css(style):
        formatter = HtmlFormatter(style=style)
        return formatter.get_style_defs('.highlight')

except ImportError:
    pygments = None

    def pygments_highlight(text, lang, style):
        return text

    def pygments_css(style):
        return None

if markdown is not None and pygments is not None:
    # starting from this blogpost and modified to support current markdown extensions API
    # https://zerokspot.com/weblog/2008/06/18/syntax-highlighting-in-markdown-with-pygments/

    from markdown.preprocessors import Preprocessor
    import re

    class CodeBlockPreprocessor(Preprocessor):
        pattern = re.compile(
            r'^\s*``` *([^\n]+)\n(.+?)^\s*```', re.M | re.S)

        formatter = HtmlFormatter()

        def run(self, lines):
            def repl(m):
                try:
                    lexer = get_lexer_by_name(m.group(1))
                except (ValueError, NameError):
                    lexer = TextLexer()
                code = m.group(2).replace('\t', '    ')
                code = pygments.highlight(code, lexer, self.formatter)
                code = code.replace('\n\n', '\n&nbsp;\n').replace('\n', '<br />').replace('\\@', '@')
                return '\n\n%s\n\n' % code
            ret = self.pattern.sub(repl, "\n".join(lines))
            return ret.split("\n")

    def md_filter_add_syntax_highlight(md):
        md.preprocessors.add('highlight', CodeBlockPreprocessor(), "_begin")
        return True
else:
    def md_filter_add_syntax_highlight(md):
        return False


# Django 1.x url routing syntax. Remove when dropping Django 1.11 support.
try:
    from django.urls import include, path, re_path, register_converter  # noqa
except ImportError:
    from django.conf.urls import include, url # noqa
    path = None
    register_converter = None
    re_path = url


# `separators` argument to `json.dumps()` differs between 2.x and 3.x
# See: https://bugs.python.org/issue22767
if six.PY3:
    SHORT_SEPARATORS = (',', ':')
    LONG_SEPARATORS = (', ', ': ')
    INDENT_SEPARATORS = (',', ': ')
else:
    SHORT_SEPARATORS = (b',', b':')
    LONG_SEPARATORS = (b', ', b': ')
    INDENT_SEPARATORS = (b',', b': ')


class CustomValidatorMessage(object):
    """
    We need to avoid evaluation of `lazy` translated `message` in `django.core.validators.BaseValidator.__init__`.
    https://github.com/django/django/blob/75ed5900321d170debef4ac452b8b3cf8a1c2384/django/core/validators.py#L297

    Ref: https://github.com/encode/django-rest-framework/pull/5452
    """

    def __init__(self, *args, **kwargs):
        self.message = kwargs.pop('message', self.message)
        super(CustomValidatorMessage, self).__init__(*args, **kwargs)


class MinValueValidator(CustomValidatorMessage, validators.MinValueValidator):
    pass


class MaxValueValidator(CustomValidatorMessage, validators.MaxValueValidator):
    pass


class MinLengthValidator(CustomValidatorMessage, validators.MinLengthValidator):
    pass


class MaxLengthValidator(CustomValidatorMessage, validators.MaxLengthValidator):
    pass


# Version Constants.
PY36 = sys.version_info >= (3, 6)
