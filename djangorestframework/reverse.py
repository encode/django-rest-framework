"""
Provide reverse functions that return fully qualified URLs
"""
from django.core.urlresolvers import reverse as django_reverse
from django.utils.functional import lazy


def reverse(viewname, *args, **kwargs):
    """
    Same as `django.core.urlresolvers.reverse`, but optionally takes a request
    and returns a fully qualified URL, using the request to get the base URL.
    """
    request = kwargs.pop('request', None)
    url = django_reverse(viewname, *args, **kwargs)
    if request:
        return request.build_absolute_uri(url)
    return url


reverse_lazy = lazy(reverse, str)
