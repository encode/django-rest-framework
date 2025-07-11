# flake8: noqa
from importlib import util as importlib_util

from .filters import *
from .filterset import FilterSet, UnknownFieldBehavior

# We make the `rest_framework` module available without an additional import.
#   If DRF is not installed, no-op.
if importlib_util.find_spec("rest_framework"):
    from . import rest_framework
del importlib_util

__version__ = "25.1"


def parse_version(version):
    """
    '0.1.2.dev1' -> (0, 1, 2, 'dev1')
    '0.1.2' -> (0, 1, 2)
    """
    v = version.split(".")
    ret = []
    for p in v:
        if p.isdigit():
            ret.append(int(p))
        else:
            ret.append(p)
    return tuple(ret)


VERSION = parse_version(__version__)
