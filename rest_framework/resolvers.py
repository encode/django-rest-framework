# coding: utf-8

import django

if django.VERSION >= (1, 10):
    from django.urls.resolvers import RegexURLPattern, RegexURLResolver
else:
    from django.core.urlresolvers import RegexURLPattern, RegexURLResolver


class DrfRegexURLPattern(RegexURLPattern):
    """
    Drf specific RegexURLPattern that can be instantiated with a router,
    for reflexion purposes.
    """
    def __init__(self, *args, **kwargs):
        self.router = kwargs.pop("router", None)
        super(DrfRegexURLPattern, self).__init__(*args, **kwargs)


class DrfRegexURLResolver(RegexURLResolver):
    """
    Drf specific RegexURLResolver that can be instantiated with a router,
    for reflexion purposes.
    """
    def __init__(self, *args, **kwargs):
        self.router = kwargs.pop("router", None)
        super(DrfRegexURLResolver, self).__init__(*args, **kwargs)


def url(regex, view, kwargs=None, name=None, router=None):
    """
    Rewrite of the django's django.conf.urls.url function, taking an extra
    'router' parameter and returning DrfRegexURLPattern or DrfRegexURLResolver
    instance instead of RegexURLPattern or RegexURLResolver.
    """
    if isinstance(view, (list, tuple)):
        # For include(...) processing.
        urlconf_module, app_name, namespace = view
        return DrfRegexURLResolver(regex, urlconf_module, kwargs, app_name=app_name, namespace=namespace, router=router)
    elif callable(view):
        return DrfRegexURLPattern(regex, view, kwargs, name, router=router)
    else:
        raise TypeError('view must be a callable or a list/tuple in the case of include().')
