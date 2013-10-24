"""
Provide reverse functions that return fully qualified URLs
"""
from __future__ import unicode_literals
from django.core.urlresolvers import reverse as django_reverse
from django.utils.functional import lazy
from django.core.urlresolvers import resolve
from django.http import Http404



def reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    """
    Same as `django.core.urlresolvers.reverse`, but optionally takes a request
    and returns a fully qualified URL, using the request to get the base URL.
    """
    if format is not None:
        kwargs = kwargs or {}
        kwargs['format'] = format

    if request:
        if hasattr(request, 'resolver_match'):
            namespace = request.resolver_match.namespace
        else:
            try:
                namespace = resolve(request.path).namespace
            except Http404:
                namespace=None

        if namespace and ':' not in viewname:
            viewname = '{namespace}:{viewname}'.format(namespace=namespace,
                                                   viewname=viewname)

    url = django_reverse(viewname, args=args, kwargs=kwargs,
                          **extra)
    if request:
        return request.build_absolute_uri(url)

    return url


reverse_lazy = lazy(reverse, str)
