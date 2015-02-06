"""
Provide urlresolver functions that return fully qualified URLs or view names
"""
from __future__ import unicode_literals
from django.core.urlresolvers import reverse as django_reverse
from django.utils import six
from django.utils.functional import lazy


def reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    """
    If versioning is being used then we pass any `reverse` calls through
    to the versioning scheme instance, so that the resulting URL
    can be modified if needed.
    """
    scheme = getattr(request, 'versioning_scheme', None)
    if scheme is not None:
        return scheme.reverse(viewname, args, kwargs, request, format, **extra)
    return _reverse(viewname, args, kwargs, request, format, **extra)


def _reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    """
    Same as `django.core.urlresolvers.reverse`, but optionally takes a request
    and returns a fully qualified URL, using the request to get the base URL.
    """
    if format is not None:
        kwargs = kwargs or {}
        kwargs['format'] = format
    url = django_reverse(viewname, args=args, kwargs=kwargs, **extra)
    if request:
        return request.build_absolute_uri(url)
    return url


reverse_lazy = lazy(reverse, six.text_type)
