"""
Provide reverse functions that return fully qualified URLs
"""
from django.core.urlresolvers import reverse as django_reverse
from djangorestframework.compat import reverse_lazy as django_reverse_lazy


def reverse(viewname, request, *args, **kwargs):
    """
    Do the same as `django.core.urlresolvers.reverse` but using
    *request* to build a fully qualified URL.
    """
    url = django_reverse(viewname, *args, **kwargs)
    return request.build_absolute_uri(url)


def reverse_lazy(viewname, request, *args, **kwargs):
    """
    Do the same as `django.core.urlresolvers.reverse_lazy` but using
    *request* to build a fully qualified URL.
    """
    url = django_reverse_lazy(viewname, *args, **kwargs)
    return request.build_absolute_uri(url)
