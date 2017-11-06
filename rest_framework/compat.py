"""
The `compat` module provides support for backwards compatibility with older
versions of Django/Python, and compatibility wrappers around optional packages.
"""

# flake8: noqa
from __future__ import unicode_literals

import inspect

import django
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.core.validators import \
    MaxLengthValidator as DjangoMaxLengthValidator
from django.core.validators import MaxValueValidator as DjangoMaxValueValidator
from django.core.validators import \
    MinLengthValidator as DjangoMinLengthValidator
from django.core.validators import MinValueValidator as DjangoMinValueValidator
from django.db import connection, models, transaction
from django.template import Context, RequestContext, Template
from django.utils import six
from django.views.generic import View

try:
    from django.urls import (
        NoReverseMatch, URLPattern as RegexURLPattern, URLResolver as RegexURLResolver, ResolverMatch, Resolver404, get_script_prefix, reverse, reverse_lazy, resolve
    )

except ImportError:
    from django.core.urlresolvers import (  # Will be removed in Django 2.0
        NoReverseMatch, RegexURLPattern, RegexURLResolver, ResolverMatch, Resolver404, get_script_prefix, reverse, reverse_lazy, resolve
    )


def get_regex_pattern(urlpattern):
    if hasattr(urlpattern, 'pattern'):
        # Django 2.0
        return urlpattern.pattern.regex.pattern
    else:
        # Django < 2.0
        return urlpattern.regex.pattern


def make_url_resolver(regex, urlpatterns):
    try:
        # Django 2.0
        from django.urls.resolvers import RegexPattern
        return RegexURLResolver(RegexPattern(regex), urlpatterns)

    except ImportError:
        # Django < 2.0
        return RegexURLResolver(regex, urlpatterns)


try:
    import urlparse  # Python 2.x
except ImportError:
    import urllib.parse as urlparse


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


def _resolve_model(obj):
    """
    Resolve supplied `obj` to a Django model class.

    `obj` must be a Django model class itself, or a string
    representation of one.  Useful in situations like GH #1225 where
    Django may not have resolved a string-based reference to a model in
    another model's foreign key definition.

    String representations should have the format:
        'appname.ModelName'
    """
    if isinstance(obj, six.string_types) and len(obj.split('.')) == 2:
        app_name, model_name = obj.split('.')
        resolved_model = apps.get_model(app_name, model_name)
        if resolved_model is None:
            msg = "Django did not return a model for {0}.{1}"
            raise ImproperlyConfigured(msg.format(app_name, model_name))
        return resolved_model
    elif inspect.isclass(obj) and issubclass(obj, models.Model):
        return obj
    raise ValueError("{0} is not a Django model".format(obj))


# django.contrib.postgres requires psycopg2
try:
    from django.contrib.postgres import fields as postgres_fields
except ImportError:
    postgres_fields = None


# coreapi is optional (Note that uritemplate is a dependency of coreapi)
try:
    import coreapi
    import uritemplate
except (ImportError, SyntaxError):
    # SyntaxError is possible under python 3.2
    coreapi = None
    uritemplate = None


# coreschema is optional
try:
    import coreschema
except ImportError:
    coreschema = None


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


# Django-guardian is optional. Import only if guardian is in INSTALLED_APPS
# Fixes (#1712). We keep the try/except for the test suite.
guardian = None
try:
    if 'guardian' in settings.INSTALLED_APPS:
        import guardian
except ImportError:
    pass


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
            r'^\s*``` *([^\n]+)\n(.+?)^\s*```', re.M|re.S)

        formatter = HtmlFormatter()

        def run(self, lines):
            def repl(m):
                try:
                    lexer = get_lexer_by_name(m.group(1))
                except (ValueError, NameError):
                    lexer = TextLexer()
                code = m.group(2).replace('\t','    ')
                code = pygments.highlight(code, lexer, self.formatter)
                code = code.replace('\n\n', '\n&nbsp;\n').replace('\n', '<br />').replace('\\@','@')
                return '\n\n%s\n\n' % code
            ret = self.pattern.sub(repl, "\n".join(lines))
            return ret.split("\n")

    def md_filter_add_syntax_highlight(md):
        md.preprocessors.add('highlight', CodeBlockPreprocessor(), "_begin")
        return True
else:
    def md_filter_add_syntax_highlight(md):
        return False

try:
    import pytz
    from pytz.exceptions import InvalidTimeError
except ImportError:
    InvalidTimeError = Exception


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


class CustomValidatorMessage(object):
    """
    We need to avoid evaluation of `lazy` translated `message` in `django.core.validators.BaseValidator.__init__`.
    https://github.com/django/django/blob/75ed5900321d170debef4ac452b8b3cf8a1c2384/django/core/validators.py#L297

    Ref: https://github.com/encode/django-rest-framework/pull/5452
    """
    def __init__(self, *args, **kwargs):
        self.message = kwargs.pop('message', self.message)
        super(CustomValidatorMessage, self).__init__(*args, **kwargs)

class MinValueValidator(CustomValidatorMessage, DjangoMinValueValidator):
    pass

class MaxValueValidator(CustomValidatorMessage, DjangoMaxValueValidator):
    pass

class MinLengthValidator(CustomValidatorMessage, DjangoMinLengthValidator):
    pass

class MaxLengthValidator(CustomValidatorMessage, DjangoMaxLengthValidator):
    pass

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


def authenticate(request=None, **credentials):
    from django.contrib.auth import authenticate
    if django.VERSION < (1, 11):
        return authenticate(**credentials)
    else:
        return authenticate(request=request, **credentials)

