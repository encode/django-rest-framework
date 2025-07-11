# -*- coding: utf-8 -*-

"""
Module for API-related calls.
"""

try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse


def hostname_tld_migration(hostname):
    """
    Migrate transifex.net to transifex.com.

    :param hostname: The hostname to migrate (if needed).
    :returns: A hostname with the transifex.com domain (if needed).
    """
    parts = urlparse.urlparse(hostname)
    if parts.hostname.endswith('transifex.net'):
        hostname = hostname.replace('transifex.net', 'transifex.com', 1)
    return hostname


def hostname_ssl_migration(hostname):
    """
    Migrate Transifex hostnames to use HTTPS.

    :param hostname: The hostname to migrate (if needed).
    :returns: A https hostname (if needed).
    """
    parts = urlparse.urlparse(hostname)
    is_transifex = (
        parts.hostname[-14:-3] == '.transifex.' or
        parts.hostname == 'transifex.net' or
        parts.hostname == 'transifex.com'
    )
    is_https = parts.scheme == 'https'
    if is_transifex and not is_https:
        if not parts.scheme:
            hostname = 'https:' + hostname
        else:
            hostname = hostname.replace(parts.scheme, 'https', 1)
    return hostname


def visit_hostname(hostname):
    """
    Have a chance to visit a hostname before actually using it.

    :param hostname: The original hostname.
    :returns: The hostname with the necessary changes.
    """
    for processor in [hostname_ssl_migration, hostname_tld_migration, ]:
        hostname = processor(hostname)
    return hostname
