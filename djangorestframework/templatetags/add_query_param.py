from django.template import Library
from urlparse import urlparse, urlunparse
from urllib import quote
register = Library()

def add_query_param(url, param):
    (key, sep, val) = param.partition('=')
    param = '%s=%s' % (key, quote(val))
    (scheme, netloc, path, params, query, fragment) = urlparse(url)
    if query:
        query += "&" + param
    else:
        query = param
    return urlunparse((scheme, netloc, path, params, query, fragment))


register.filter('add_query_param', add_query_param)
