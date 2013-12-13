from __future__ import unicode_literals
from django.conf.urls import url, include
from django.core.urlresolvers import RegexURLResolver
from rest_framework.settings import api_settings


def apply_suffix_patterns(urlpatterns, suffix_pattern, suffix_required):
    ret = []
    for urlpattern in urlpatterns:
        if isinstance(urlpattern, RegexURLResolver):
            # Set of included URL patterns
            regex = urlpattern.regex.pattern
            namespace = urlpattern.namespace
            app_name = urlpattern.app_name
            kwargs = urlpattern.default_kwargs
            # Add in the included patterns, after applying the suffixes
            patterns = apply_suffix_patterns(urlpattern.url_patterns,
                                             suffix_pattern,
                                             suffix_required)
            ret.append(url(regex, include(patterns, namespace, app_name), kwargs))

        else:
            # Regular URL pattern
            regex = urlpattern.regex.pattern.rstrip('$') + suffix_pattern
            view = urlpattern._callback or urlpattern._callback_str
            kwargs = urlpattern.default_args
            name = urlpattern.name
            # Add in both the existing and the new urlpattern
            if not suffix_required:
                ret.append(urlpattern)
            ret.append(url(regex, view, kwargs, name))

    return ret


def format_suffix_patterns(urlpatterns, suffix_required=False, allowed=None):
    """
    Supplement existing urlpatterns with corresponding patterns that also
    include a '.format' suffix.  Retains urlpattern ordering.

    urlpatterns:
        A list of URL patterns.

    suffix_required:
        If `True`, only suffixed URLs will be generated, and non-suffixed
        URLs will not be used.  Defaults to `False`.

    allowed:
        An optional tuple/list of allowed suffixes.  eg ['json', 'api']
        Defaults to `None`, which allows any suffix.
    """
    suffix_kwarg = api_settings.FORMAT_SUFFIX_KWARG
    if allowed:
        if len(allowed) == 1:
            allowed_pattern = allowed[0]
        else:
            allowed_pattern = '(%s)' % '|'.join(allowed)
        suffix_pattern = r'\.(?P<%s>%s)$' % (suffix_kwarg, allowed_pattern)
    else:
        suffix_pattern = r'\.(?P<%s>[a-z0-9]+)$' % suffix_kwarg

    return apply_suffix_patterns(urlpatterns, suffix_pattern, suffix_required)
