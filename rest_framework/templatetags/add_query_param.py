from django.http import QueryDict
from django.template import Library
from urlparse import urlparse, urlunparse
register = Library()


def replace_query_param(url, key, val):
    (scheme, netloc, path, params, query, fragment) = urlparse(url)
    query_dict = QueryDict(query).copy()
    query_dict[key] = val
    query = query_dict.urlencode()
    return urlunparse((scheme, netloc, path, params, query, fragment))


def add_query_param(url, param):
    key, val = param.split('=')
    return replace_query_param(url, key, val)


register.filter('add_query_param', add_query_param)
