"""
Provide reverse functions that return fully qualified URLs
"""
from django.core.urlresolvers import reverse as django_reverse
from django.utils.functional import lazy
from rest_framework.settings import api_settings


def reverse(viewname, args=None, kwargs=None, request=None, format=None, use_absolute_urls=api_settings.USE_ABSOLUTE_URLS, **extra):
    """
    Same as `django.core.urlresolvers.reverse`, but optionally takes a request
    and returns a fully qualified URL, using the request to get the base URL.
    """
    if format is not None:
        kwargs = kwargs or {}
        kwargs['format'] = format
    url = django_reverse(viewname, args=args, kwargs=kwargs, **extra)
    if use_absolute_urls:
        assert request, "request is required for building absolute url"
        url = request.build_absolute_uri(url)
    return url


reverse_lazy = lazy(reverse, str)
