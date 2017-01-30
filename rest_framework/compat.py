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
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models, transaction
from django.template import Context, RequestContext, Template
from django.utils import six
from django.views.generic import View


try:
    from django.urls import (
        NoReverseMatch, RegexURLPattern, RegexURLResolver, ResolverMatch, Resolver404, get_script_prefix, reverse, reverse_lazy, resolve
    )
except ImportError:
    from django.core.urlresolvers import (  # Will be removed in Django 2.0
        NoReverseMatch, RegexURLPattern, RegexURLResolver, ResolverMatch, Resolver404, get_script_prefix, reverse, reverse_lazy, resolve
    )


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


# Obtaining manager instances and names from model options differs after 1.10.
def get_names_and_managers(options):
    if django.VERSION >= (1, 10):
        # Django 1.10 onwards provides a `.managers` property on the Options.
        return [
            (manager.name, manager)
            for manager
            in options.managers
        ]
    # For Django 1.8 and 1.9, use the three-tuple information provided
    # by .concrete_managers and .abstract_managers
    return [
        (manager_info[1], manager_info[2])
        for manager_info
        in (options.concrete_managers + options.abstract_managers)
    ]


# field.rel is deprecated from 1.9 onwards
def get_remote_field(field, **kwargs):
    if 'default' in kwargs:
        if django.VERSION < (1, 9):
            return getattr(field, 'rel', kwargs['default'])
        return getattr(field, 'remote_field', kwargs['default'])

    if django.VERSION < (1, 9):
        return field.rel
    return field.remote_field


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


def is_authenticated(user):
    if django.VERSION < (1, 10):
        return user.is_authenticated()
    return user.is_authenticated


def is_anonymous(user):
    if django.VERSION < (1, 10):
        return user.is_anonymous()
    return user.is_anonymous


def get_related_model(field):
    if django.VERSION < (1, 9):
        return _resolve_model(field.rel.to)
    return field.remote_field.model


def value_from_object(field, obj):
    if django.VERSION < (1, 9):
        return field._get_val_from_obj(obj)
    return field.value_from_object(obj)


# contrib.postgres only supported from 1.8 onwards.
try:
    from django.contrib.postgres import fields as postgres_fields
except ImportError:
    postgres_fields = None


# JSONField is only supported from 1.9 onwards
try:
    from django.contrib.postgres.fields import JSONField
except ImportError:
    JSONField = None


# coreapi is optional (Note that uritemplate is a dependency of coreapi)
try:
    import coreapi
    import uritemplate
except (ImportError, SyntaxError):
    # SyntaxError is possible under python 3.2
    coreapi = None
    uritemplate = None


# django-filter is optional
try:
    import django_filters
except ImportError:
    django_filters = None


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

try:
    # DecimalValidator is unavailable in Django < 1.9
    from django.core.validators import DecimalValidator
except ImportError:
    DecimalValidator = None


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


def template_render(template, context=None, request=None):
    """
    Passing Context or RequestContext to Template.render is deprecated in 1.9+,
    see https://github.com/django/django/pull/3883 and
    https://github.com/django/django/blob/1.9/django/template/backends/django.py#L82-L84

    :param template: Template instance
    :param context: dict
    :param request: Request instance
    :return: rendered template as SafeText instance
    """
    if isinstance(template, Template):
        if request:
            context = RequestContext(request, context)
        else:
            context = Context(context)
        return template.render(context)
    # backends template, e.g. django.template.backends.django.Template
    else:
        return template.render(context, request=request)


def set_many(instance, field, value):
    if django.VERSION < (1, 10):
        setattr(instance, field, value)
    else:
        field = getattr(instance, field)
        field.set(value)

def include(module, namespace=None, app_name=None):
    from django.conf.urls import include
    if django.VERSION < (1,9):
        return include(module, namespace, app_name)
    else:
        return include((module, app_name), namespace)
