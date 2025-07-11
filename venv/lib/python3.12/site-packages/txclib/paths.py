# -*- coding: utf-8 -*-

"""
Path handling.

We need to take into account the differences between UNIX systems and
Windows.
"""

import os


posix_sep = os.sep if os.altsep is None else os.altsep


def posix_path(fpath):
    """Convert a filesystem path to a posix path.

    Always use the forward slash as a separator. For instance,
    in windows the separator is the backslash.

    Args:
        fpath: The path to convert.
    """
    return fpath if os.altsep is None else fpath.replace(os.sep, os.altsep)


def native_path(fpath):
    """Convert a filesystem path to a native path.

    Use whatever separator is defined by the platform.

    Args:
        fpath: The path to convert.
    """
    return fpath if os.altsep is None else fpath.replace(os.altsep, os.sep)
