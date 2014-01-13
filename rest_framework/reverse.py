"""
Provide reverse functions that return fully qualified URLs
"""
from __future__ import unicode_literals
from django.core.urlresolvers import reverse as django_reverse
from django.utils.functional import lazy
from rest_framework.settings import api_settings


def reverse(viewname, args=None, kwargs=None, request=None, format=None, force_absolute=False, **extra):
    """
    Same as `django.core.urlresolvers.reverse`, but optionally takes a request
    and returns a fully qualified URL, using the request to get the base URL.
    """
    if format is not None:
        kwargs = kwargs or {}
        kwargs['format'] = format
    url = django_reverse(viewname, args=args, kwargs=kwargs, **extra)

    if api_settings.RELATIVE_URLS and not force_absolute:
        return url
    if request:
        return request.build_absolute_uri(url)
    return url


reverse_lazy = lazy(reverse, str)
