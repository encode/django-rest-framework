"""
Provide urlresolver functions that return fully qualified URLs or view names
"""
from __future__ import unicode_literals

from django.conf import settings, urls
from django.core.urlresolvers import reverse as django_reverse
from django.core.urlresolvers import NoReverseMatch, resolve
from django.http import Http404
from django.utils import six
from django.utils.functional import lazy

from rest_framework.settings import api_settings
from rest_framework.utils.urls import replace_query_param


def preserve_builtin_query_params(url, request=None):
    """
    Given an incoming request, and an outgoing URL representation,
    append the value of any built-in query parameters.
    """
    if request is None:
        return url

    overrides = [
        api_settings.URL_FORMAT_OVERRIDE,
    ]

    for param in overrides:
        if param and (param in request.GET):
            value = request.GET[param]
            url = replace_query_param(url, param, value)

    return url


def reverse(viewname, args=None, kwargs=None, request=None, format=None, **extra):
    """
    If versioning is being used then we pass any `reverse` calls through
    to the versioning scheme instance, so that the resulting URL can be modified if needed.
    """
    url = None

    # Substitute reverse function by scheme's one if versioning enabled
    scheme = getattr(request, 'versioning_scheme', None)
    if scheme is not None:
        def reverse_url(*a, **kw):
            try:
                return scheme.reverse(*a, **kw)
            except NoReverseMatch:
                # In case the versioning scheme reversal fails, fallback to the default implementation
                return _reverse(*a, **kw)
    else:
        reverse_url = _reverse

    try:
        # Resolving URL normally
        url = reverse_url(viewname, args, kwargs, request, format, **extra)
    except NoReverseMatch:
        if request and ':' not in viewname:
            # Retrieving current namespace through request
            try:
                current_namespace = request.resolver_match.namespace
            except AttributeError:
                try:
                    current_namespace = resolve(request.path).namespace
                except Http404:
                    current_namespace = None

            if current_namespace:
                try:
                    # Trying to resolve URL with current namespace
                    viewname_to_try = '{namespace}:{viewname}'.format(namespace=current_namespace, viewname=viewname)
                    url = reverse_url(viewname_to_try, args, kwargs, request, format, **extra)
                except NoReverseMatch:
                    # Trying to resolve URL with other namespaces
                    # (Could be wrong if views have the same name in different namespaces)
                    urlpatterns = urls.import_module(settings.ROOT_URLCONF).urlpatterns
                    namespaces = [urlpattern.namespace for urlpattern in urlpatterns
                                  if getattr(urlpattern, 'namespace', current_namespace) != current_namespace]

                    # Remove duplicates but preserve order of elements
                    from collections import OrderedDict
                    for namespace in OrderedDict.fromkeys(namespaces):
                        try:
                            viewname_to_try = '{namespace}:{viewname}'.format(namespace=namespace, viewname=viewname)
                            url = reverse_url(viewname_to_try, args, kwargs, request, format, **extra)
                            break
                        except NoReverseMatch:
                            continue
        # Raise exception if everything else fails
        if not url:
            raise
    return preserve_builtin_query_params(url, request)


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
