# -*- coding: utf-8 -*-
"""
Contains the crawling logic.
"""
from __future__ import unicode_literals, absolute_import

import re

from pylinkvalidator.compat import urlparse, quote


SCHEME_HTTP = "http"
SCHEME_HTTPS = "https"
SUPPORTED_SCHEMES = (SCHEME_HTTP, SCHEME_HTTPS)


NOT_LINK = [
    'data',
    '#',
]


def is_link(url):
    """Return True if the url is not base 64 data or a local ref (#)"""
    for prefix in NOT_LINK:
        if url.startswith(prefix):
            return False
    return True


def get_clean_url_split(url):
    """Returns a clean SplitResult with a scheme and a valid path

    :param url: The url to clean
    :rtype: A urlparse.SplitResult
    """
    if not url:
        raise ValueError('The URL must not be empty')
    split_result = urlparse.urlsplit(url)

    if not split_result.scheme:
        if split_result.netloc:
            url = SCHEME_HTTP + ":" + url
        else:
            url = SCHEME_HTTP + "://" + url
        split_result = urlparse.urlsplit(url)

    split_result = convert_iri_to_uri(split_result)

    return split_result


def convert_iri_to_uri(url_split):
    """Attempts to convert potential IRI to URI.

    IRI may contain non-ascii characters.
    """
    new_parts = []
    for i, part in enumerate(url_split):
        if i == 1:
            # domain name
            new_parts.append(part.encode('idna').decode('ascii'))
        else:
            # other parts such as path or query string.
            new_parts.append(url_encode_non_ascii(part))
    return urlparse.SplitResult(*new_parts)


def url_encode_non_ascii(url_part):
    """For each byte in url_part, if the byte is outside ascii range, quote the
    byte. UTF characters that take two bytes will be correctly converted using
    this technique.

    We do not quote the whole url part because it might contain already quoted
    characters, which would then be double-quoted.

    The url part is converted from utf-8 and then to utf-8, which might not
    always work if there is mixed or bad encoding.
    """
    return re.sub(
        b'[\x80-\xFF]',
        lambda match: quote(match.group(0)).encode("utf-8"),
        url_part.encode("utf-8")).decode("ascii")


def get_absolute_url_split(url, base_url_split):
    """Returns a SplitResult containing the new URL.

    :param url: The url (relative or absolute).
    :param base_url_split: THe SplitResult of the base URL.
    :rtype: A SplitResult
    """
    new_url = urlparse.urljoin(base_url_split.geturl(), url)

    return get_clean_url_split(new_url)
