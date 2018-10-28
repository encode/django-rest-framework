from django.utils.encoding import force_str
from django.utils.six.moves.urllib import parse as urlparse


def replace_query_param(url, key, val):
    """
    Given a URL and a key/val pair, set or replace an item in the query
    parameters of the URL, and return the new URL.
    """
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(force_str(url))
    query_dict = urlparse.parse_qs(query, keep_blank_values=True)
    query_dict[force_str(key)] = [force_str(val)]
    query = urlparse.urlencode(sorted(list(query_dict.items())), doseq=True)
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


def remove_query_param(url, key):
    """
    Given a URL and a key/val pair, remove an item in the query
    parameters of the URL, and return the new URL.
    """
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(force_str(url))
    query_dict = urlparse.parse_qs(query, keep_blank_values=True)
    query_dict.pop(key, None)
    query = urlparse.urlencode(sorted(list(query_dict.items())), doseq=True)
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))
