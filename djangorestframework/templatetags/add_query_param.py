from django.template import Library
from urlobject import URLObject
register = Library()


def add_query_param(url, param):
    return unicode(URLObject(url).with_query(param))


register.filter('add_query_param', add_query_param)
