from django.template import Library
from urlobject import URLObject
register = Library()


def add_query_param(url, param):
    (key, sep, val) = param.partition('=')
    return unicode(URLObject.parse(url) & (key, val))


register.filter('add_query_param', add_query_param)
