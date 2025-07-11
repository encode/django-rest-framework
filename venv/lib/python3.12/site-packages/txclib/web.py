# -*- coding: utf-8 -*-

import os
import platform
from pkg_resources import resource_filename, resource_string
import txclib


def user_agent_identifier():
    """Return the user agent for the client."""
    client_info = (txclib.__version__, platform.system(), platform.machine())
    return "txclient/%s (%s %s)" % client_info


def certs_file():
    if platform.system() == 'Windows':
        return os.path.join(txclib.utils.get_base_dir(), 'cacert.pem')
    else:
        POSSIBLE_CA_BUNDLE_PATHS = [
            # Red Hat, CentOS, Fedora and friends
            # (provided by the ca-certificates package):
            '/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem',
            '/etc/ssl/certs/ca-bundle.crt',
            '/etc/pki/tls/certs/ca-bundle.crt',
            # Ubuntu, Debian, and friends
            # (provided by the ca-certificates package):
            '/etc/ssl/certs/ca-certificates.crt',
            # FreeBSD (provided by the ca_root_nss package):
            '/usr/local/share/certs/ca-root-nss.crt',
            # openSUSE (provided by the ca-certificates package),
            # the 'certs' directory is the
            # preferred way but may not be supported by the SSL module,
            # thus it has 'ca-bundle.pem'
            # as a fallback (which is generated from pem files in the
            # 'certs' directory):
            '/etc/ssl/ca-bundle.pem',
        ]
        for path in POSSIBLE_CA_BUNDLE_PATHS:
            if os.path.exists(path):
                return path
        return resource_filename(__name__, 'cacert.pem')
