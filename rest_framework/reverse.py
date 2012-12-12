"""
Provide reverse functions that return fully qualified URLs
"""
from rest_framework.settings import api_settings
from django.core.urlresolvers import reverse as django_reverse
from django.utils.functional import lazy


def reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    """
    Same as `django.core.urlresolvers.reverse`, but optionally takes a request
    and returns a fully qualified URL, using the request to get the base URL.
    """
    if format is not None:
        kwargs = kwargs or {}
        kwargs['format'] = format
    url = django_reverse(viewname, args=args, kwargs=kwargs, **extra)
    if api_settings.USE_ABSOLUTE_URLS:
        assert request, "request is required for building absolute url"
        url = request.build_absolute_uri(url)
    return url


reverse_lazy = lazy(reverse, str)
